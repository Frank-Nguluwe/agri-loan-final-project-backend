from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.config.database import get_db
from app.models.db_models import (
    User, LoanApplication, ApplicationReview, District, UserRole, ApplicationStatus, ReviewAction
)

from app.schemas.supervisor_schemas import ApplicationApprovalRequest, ApplicationApprovalResponse, DashboardMetrics, LoanOfficerStats, LoanOfficerSummary
from app.utils.dependencies import require_supervisor
from app.utils.supervisor_utils import check_supervisor_permissions, get_managed_loan_officers, get_supervisor_districts

router = APIRouter(prefix="/supervisors", tags=["supervisors"])


@router.get("/dashboard", response_model=DashboardMetrics)
def get_supervisor_dashboard(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
    period_days: Optional[int] = 30
):
    """Get comprehensive dashboard metrics for supervisor"""
    
    if not check_supervisor_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Supervisor role required."
        )
    
    # Get accessible districts
    accessible_districts = get_supervisor_districts(current_user, db)
    
    if not accessible_districts:
        # Return empty dashboard if no districts accessible
        return DashboardMetrics(
            total_applications=0,
            approved_applications=0,
            pending_applications=0,
            rejected_applications=0,
            total_amount_approved=0.0,
            average_approval_amount=0.0,
            approval_rate=0.0,
            loan_officer_stats=[],
            monthly_trends={},
            district_summary={}
        )
    
    # Base query for applications in accessible districts
    base_query = db.query(LoanApplication).filter(
        LoanApplication.district_id.in_(accessible_districts)
    )
    
    # Get basic statistics
    total_applications = base_query.count()
    
    approved_applications = base_query.filter(
        LoanApplication.status == ApplicationStatus.APPROVED
    ).count()
    
    pending_applications = base_query.filter(
        LoanApplication.status.in_([
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW
        ])
    ).count()
    
    rejected_applications = base_query.filter(
        LoanApplication.status == ApplicationStatus.REJECTED
    ).count()
    
    # Calculate financial metrics
    approved_amount_result = base_query.filter(
        and_(
            LoanApplication.status == ApplicationStatus.APPROVED,
            LoanApplication.approved_amount_mwk.isnot(None)
        )
    ).with_entities(
        func.sum(LoanApplication.approved_amount_mwk),
        func.avg(LoanApplication.approved_amount_mwk)
    ).first()
    
    total_amount_approved = float(approved_amount_result[0]) if approved_amount_result[0] else 0.0
    average_approval_amount = float(approved_amount_result[1]) if approved_amount_result[1] else 0.0
    
    # Calculate approval rate
    approval_rate = (approved_applications / total_applications * 100) if total_applications > 0 else 0.0
    
    # Get loan officer statistics
    managed_officers = get_managed_loan_officers(current_user, db)
    loan_officer_stats = []
    
    for officer in managed_officers:
        officer_query = base_query.filter(
            LoanApplication.farmer_id.in_(
                db.query(User.id).filter(
                    and_(
                        User.role == UserRole.FARMER,
                        User.district_id == officer.district_id
                    )
                ).subquery()
            )
        )
        
        officer_total = officer_query.count()
        officer_approved = officer_query.filter(
            LoanApplication.status == ApplicationStatus.APPROVED
        ).count()
        officer_pending = officer_query.filter(
            LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW
            ])
        ).count()
        
        # Calculate average processing time
        completed_apps = officer_query.filter(
            LoanApplication.status.in_([
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED
            ])
        ).all()
        
        avg_processing_time = None
        if completed_apps:
            total_days = sum([
                (app.approval_date - app.application_date).days
                for app in completed_apps
                if app.approval_date and app.application_date
            ])
            avg_processing_time = total_days / len(completed_apps) if completed_apps else None
        
        loan_officer_stats.append(LoanOfficerStats(
            officer_id=str(officer.id),
            name=f"{officer.first_name} {officer.last_name}",
            active_applications=officer_pending,
            total_applications=officer_total,
            approved_applications=officer_approved,
            pending_applications=officer_pending,
            avg_processing_time_days=avg_processing_time,
            district_name=officer.district_rel.name if officer.district_rel else "Unknown"
        ))
    
    # Get monthly trends (last 6 months)
    monthly_trends = {}
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_applications = base_query.filter(
            and_(
                LoanApplication.application_date >= month_start,
                LoanApplication.application_date < month_end
            )
        ).count()
        
        month_approvals = base_query.filter(
            and_(
                LoanApplication.application_date >= month_start,
                LoanApplication.application_date < month_end,
                LoanApplication.status == ApplicationStatus.APPROVED
            )
        ).count()
        
        monthly_trends[month_start.strftime("%Y-%m")] = {
            "applications": month_applications,
            "approvals": month_approvals
        }
    
    # Get district summary
    district_summary = {}
    for district_id in accessible_districts:
        district = db.query(District).filter(District.id == district_id).first()
        if district:
            district_apps = base_query.filter(LoanApplication.district_id == district_id).count()
            district_approved = base_query.filter(
                and_(
                    LoanApplication.district_id == district_id,
                    LoanApplication.status == ApplicationStatus.APPROVED
                )
            ).count()
            
            district_summary[district.name] = {
                "total_applications": district_apps,
                "approved_applications": district_approved,
                "approval_rate": (district_approved / district_apps * 100) if district_apps > 0 else 0.0
            }
    
    return DashboardMetrics(
        total_applications=total_applications,
        approved_applications=approved_applications,
        pending_applications=pending_applications,
        rejected_applications=rejected_applications,
        total_amount_approved=total_amount_approved,
        average_approval_amount=average_approval_amount,
        approval_rate=approval_rate,
        loan_officer_stats=loan_officer_stats,
        monthly_trends=monthly_trends,
        district_summary=district_summary
    )

@router.get("/loan-officers", response_model=List[LoanOfficerSummary])
def get_loan_officers(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """Get list of loan officers managed by supervisor"""
    
    if not check_supervisor_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Supervisor role required."
        )
    
    # Get managed loan officers
    managed_officers = get_managed_loan_officers(current_user, db)
    
    result = []
    for officer in managed_officers:
        # Get application counts for this officer
        officer_applications = db.query(LoanApplication).join(
            User, LoanApplication.farmer_id == User.id
        ).filter(
            and_(
                User.role == UserRole.FARMER,
                User.district_id == officer.district_id
            )
        )
        
        total_applications = officer_applications.count()
        active_applications = officer_applications.filter(
            LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW
            ])
        ).count()
        
        # Get assignment date (if available)
        assignment_date = None
        if current_user.role == UserRole.SUPERVISOR:
            assignment = db.query(User).join(
                "supervisor_loan_officer",
                and_(
                    User.id == officer.id,
                    User.supervisor_loan_officer.c.supervisor_id == current_user.id
                )
            ).first()
            if assignment:
                assignment_date = assignment.created_at  # You might need to adjust this
        
        result.append(LoanOfficerSummary(
            officer_id=str(officer.id),
            name=f"{officer.first_name} {officer.last_name}",
            email=officer.email,
            phone_number=officer.phone_number,
            active_applications=active_applications,
            total_applications=total_applications,
            district_name=officer.district_rel.name if officer.district_rel else "Unknown",
            is_active=officer.is_active,
            assigned_date=assignment_date
        ))
    
    return result

@router.put("/applications/{application_id}/approve", response_model=ApplicationApprovalResponse)
def approve_reject_application(
    application_id: UUID,
    approval_request: ApplicationApprovalRequest,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """Approve or reject a loan application with optional override"""
    
    # Permission checks remain the same
    if not check_supervisor_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Supervisor role required."
        )
    
    # Get application
    application = db.query(LoanApplication).options(
        joinedload(LoanApplication.farmer),
        joinedload(LoanApplication.district_rel)
    ).filter(LoanApplication.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )
    
    # District access check
    accessible_districts = get_supervisor_districts(current_user, db)
    if str(application.district_id) not in accessible_districts:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this application's district"
        )
    
    # Status validation
    if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=400,
            detail=f"Application cannot be {approval_request.action}d from status: {application.status.value}"
        )
    
    # Process the approval/rejection
    if approval_request.action.lower() == "approve":
        # Determine the approved amount
        if approval_request.override_prediction:
            # Use explicitly provided amount when override is True
            approved_amount = approval_request.approved_amount_mwk
            if not approved_amount or approved_amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="approved_amount_mwk must be positive when overriding prediction"
                )
            
            # Validate override reason is provided
            if not approval_request.override_reason:
                raise HTTPException(
                    status_code=400,
                    detail="override_reason is required when override_prediction is True"
                )
        else:
            # Use predicted amount when override is False
            if not application.predicted_amount_mwk:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot approve - no predicted amount available and override is False"
                )
            approved_amount = float(application.predicted_amount_mwk)
        
        # Update application
        application.status = ApplicationStatus.APPROVED
        application.approved_amount_mwk = approved_amount
        application.approval_date = datetime.now()
        application.approved_by = current_user.id
        
        if approval_request.override_prediction:
            application.override_reason = approval_request.override_reason
        
        # Create approval review record
        review = ApplicationReview(
            application_id=application.id,
            reviewer_id=current_user.id,
            comments=approval_request.comments or (
                f"Approved for {approved_amount:,.2f} MWK" +
                (" (override)" if approval_request.override_prediction else " (auto-approved predicted amount)")
            ),
            action=ReviewAction.RECOMMEND_APPROVAL
        )
        db.add(review)
        
        response_message = f"Application approved for {approved_amount:,.2f} MWK"
        if approval_request.override_prediction:
            response_message += " (with override)"
        else:
            response_message += " (using predicted amount)"
    
    elif approval_request.action.lower() == "reject":
        # Rejection logic remains the same
        application.status = ApplicationStatus.REJECTED
        application.approval_date = datetime.now()
        application.approved_by = current_user.id
        
        review = ApplicationReview(
            application_id=application.id,
            reviewer_id=current_user.id,
            comments=approval_request.comments or "Application rejected",
            action=ReviewAction.REJECT
        )
        db.add(review)
        
        response_message = "Application rejected"
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Action must be 'approve' or 'reject'"
        )
    
    # Commit changes
    db.commit()
    db.refresh(application)
    
    return ApplicationApprovalResponse(
        message=response_message,
        application_id=str(application.id),
        new_status=application.status.value,
        approved_amount=float(application.approved_amount_mwk) if application.approved_amount_mwk else None,
        approval_date=application.approval_date
    )

# Additional utility endpoints
@router.get("/applications/pending")
def get_pending_applications(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get pending applications requiring supervisor attention"""
    
    if not check_supervisor_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Supervisor role required."
        )
    
    accessible_districts = get_supervisor_districts(current_user, db)
    
    if not accessible_districts:
        return []
    
    # Get applications that need supervisor attention
    applications = db.query(LoanApplication).options(
        joinedload(LoanApplication.farmer),
        joinedload(LoanApplication.crop_type_rel),
        joinedload(LoanApplication.district_rel)
    ).filter(
        and_(
            LoanApplication.district_id.in_(accessible_districts),
            LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW
            ])
        )
    ).order_by(LoanApplication.application_date).offset(offset).limit(limit).all()
    
    return [
        {
            "application_id": str(app.id),
            "farmer_name": f"{app.farmer.first_name} {app.farmer.last_name}",
            "application_date": app.application_date,
            "crop_type": app.crop_type_rel.name,
            "predicted_amount_mwk": float(app.predicted_amount_mwk) if app.predicted_amount_mwk else None,
            "prediction_confidence": float(app.prediction_confidence) if app.prediction_confidence else None,
            "expected_revenue_mwk": float(app.expected_revenue_mwk),
            "district_name": app.district_rel.name,
            "status": app.status.value,
            "days_pending": (datetime.now() - app.application_date).days
        }
        for app in applications
    ]

@router.post("/applications/{application_id}/assign")
def assign_application_to_officer(
    application_id: str,
    officer_id: str,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """Assign application to specific loan officer for review"""
    
    if not check_supervisor_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Supervisor role required."
        )
    
    # Get application
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )
    
    # Verify supervisor has access to this application
    accessible_districts = get_supervisor_districts(current_user, db)
    if str(application.district_id) not in accessible_districts:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this application's district"
        )
    
    # Get loan officer
    officer = db.query(User).filter(
        and_(
            User.id == officer_id,
            User.role == UserRole.LOAN_OFFICER
        )
    ).first()
    
    if not officer:
        raise HTTPException(
            status_code=404,
            detail="Loan officer not found"
        )
    
    # Verify officer is managed by supervisor
    managed_officers = get_managed_loan_officers(current_user, db)
    if officer not in managed_officers:
        raise HTTPException(
            status_code=403,
            detail="You can only assign applications to loan officers under your supervision"
        )
    
    # Update application status
    application.status = ApplicationStatus.UNDER_REVIEW
    
    # Create assignment review record
    review = ApplicationReview(
        application_id=application.id,
        reviewer_id=current_user.id,
        comments=f"Assigned to {officer.first_name} {officer.last_name} for review",
        action=ReviewAction.REQUEST_CHANGES  # Using this as "assigned" action
    )
    db.add(review)
    
    db.commit()
    
    return {
        "message": f"Application assigned to {officer.first_name} {officer.last_name}",
        "application_id": str(application.id),
        "assigned_officer": f"{officer.first_name} {officer.last_name}",
        "new_status": application.status.value
    }