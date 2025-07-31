from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional
from app.config.database import get_db
from app.models.db_models import (
    User, LoanApplication, ApplicationReview, 
    CropType, District, YieldHistory, ApplicationStatus
)
from app.schemas.loan_officer_schema import ApplicationFullDetails, ApplicationListItem, ApplicationReviewHistory, FarmerProfileDetail, PredictionDetails, YieldHistoryItem
from app.utils.dependencies import require_loan_officer
from app.utils.loan_officer_utils import check_loan_officer_permissions, get_accessible_districts

router = APIRouter(prefix="/loan-officers", tags=["loan-officers"])


@router.get("/applications", response_model=List[ApplicationListItem])
def get_applications(
    current_user: User = Depends(require_loan_officer),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, etc.)"),
    district_id: Optional[str] = Query(None, description="Filter by district ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of applications to return"),
    offset: int = Query(0, ge=0, description="Number of applications to skip"),
    sort_by: str = Query("application_date", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get loan applications filtered by various criteria"""
    
    # Check permissions
    # if not check_loan_officer_permissions(current_user, district_id):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Insufficient permissions to view applications"
    #     )
    
    # Get accessible districts
    accessible_districts = get_accessible_districts(current_user, db)
    
    if not accessible_districts:
        raise HTTPException(
            status_code=403,
            detail="No accessible districts found"
        )
    
    # Build query
    query = db.query(LoanApplication).options(
        joinedload(LoanApplication.farmer),
        joinedload(LoanApplication.crop_type_rel),
        joinedload(LoanApplication.district_rel)
    )
    
    # Apply district filter
    if district_id:
        if district_id not in accessible_districts:
            raise HTTPException(
                status_code=403,
                detail="Access denied to specified district"
            )
        query = query.filter(LoanApplication.district_id == district_id)
    else:
        query = query.filter(LoanApplication.district_id.in_(accessible_districts))
    
    # Apply status filter
    if status:
        if status.lower() == "pending":
            # "Pending" means submitted and under review
            query = query.filter(LoanApplication.status.in_([
                ApplicationStatus.SUBMITTED, 
                ApplicationStatus.UNDER_REVIEW
            ]))
        else:
            try:
                status_enum = ApplicationStatus(status.lower())
                query = query.filter(LoanApplication.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
    
    # Apply sorting
    if sort_by == "application_date":
        sort_column = LoanApplication.application_date
    elif sort_by == "predicted_amount":
        sort_column = LoanApplication.predicted_amount_mwk
    elif sort_by == "farmer_name":
        sort_column = User.first_name  # Will need to join properly
    else:
        sort_column = LoanApplication.application_date
    
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    applications = query.offset(offset).limit(limit).all()
    
    # Format response
    result = []
    for app in applications:
        result.append(ApplicationListItem(
            application_id = app.id,
            farmer_name=f"{app.farmer.first_name} {app.farmer.last_name}",
            application_date=app.application_date,
            predicted_amount_mwk=float(app.predicted_amount_mwk) if app.predicted_amount_mwk else None,
            status=app.status.value,
            crop_type=app.crop_type_rel.name,
            farm_size_hectares=float(app.farm_size_hectares),
            district_name=app.district_rel.name,
            expected_yield_kg=float(app.expected_yield_kg),
            expected_revenue_mwk=float(app.expected_revenue_mwk)
        ))
    
    return result

@router.get("/applications/{application_id}", response_model=ApplicationFullDetails)
def get_application_details(
    application_id: str,
    current_user: User = Depends(require_loan_officer),
    db: Session = Depends(get_db)
):
    """Get detailed application information for review"""
    
    # Get application with all related data
    application = db.query(LoanApplication).options(
        joinedload(LoanApplication.farmer).joinedload(User.farmer_profile),
        joinedload(LoanApplication.farmer).joinedload(User.district_rel),
        joinedload(LoanApplication.crop_type_rel),
        joinedload(LoanApplication.district_rel),
        joinedload(LoanApplication.reviews).joinedload(ApplicationReview.reviewer),
        joinedload(LoanApplication.approver)
    ).filter(LoanApplication.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )
    
    # Check permissions
    # if not check_loan_officer_permissions(current_user, str(application.district_id)):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Insufficient permissions to view this application"
        # )
    
    # Verify user can access this district
    accessible_districts = get_accessible_districts(current_user, db)
    if str(application.district_id) not in accessible_districts:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this application's district"
        )
    
    # Get farmer profile
    farmer = application.farmer
    farmer_profile = farmer.farmer_profile
    
    farmer_profile_detail = FarmerProfileDetail(
        user_id=farmer.id,
        email=farmer.email,
        phone_number=farmer.phone_number,
        first_name=farmer.first_name,
        last_name=farmer.last_name,
        date_of_birth=farmer_profile.date_of_birth if farmer_profile else None,
        national_id=farmer_profile.national_id if farmer_profile else None,
        address=farmer_profile.address if farmer_profile else None,
        farm_location_gps=farmer_profile.farm_location_gps if farmer_profile else None,
        farm_size_hectares=float(farmer_profile.farm_size_hectares) if farmer_profile and farmer_profile.farm_size_hectares else None,
        registration_date=farmer.created_at,
        district_name=farmer.district_rel.name if farmer.district_rel else None
    )
    
    # Get yield history
    yield_history = []
    if farmer_profile:
        yield_records = db.query(YieldHistory).filter(
            YieldHistory.farmer_id == farmer_profile.id
        ).join(
            CropType, YieldHistory.crop_type_id == CropType.id
        ).order_by(desc(YieldHistory.year)).all()
        
        yield_history = [
            YieldHistoryItem(
                year=record.year,
                crop_type=record.crop_type_rel.name,
                yield_amount_kg=float(record.yield_amount_kg) if record.yield_amount_kg else None,
                revenue_mwk=float(record.revenue_mwk) if record.revenue_mwk else None
            )
            for record in yield_records
        ]
    
    # Get prediction details
    prediction_details = PredictionDetails(
        predicted_amount_mwk=float(application.predicted_amount_mwk) if application.predicted_amount_mwk else None,
        prediction_confidence=float(application.prediction_confidence) if application.prediction_confidence else None,
        prediction_date=application.prediction_date
    )
    
    # Get review history
    review_history = [
        ApplicationReviewHistory(
            reviewer_name=f"{review.reviewer.first_name} {review.reviewer.last_name}",
            review_date=review.review_date,
            comments=review.comments,
            action=review.action.value
        )
        for review in application.reviews
    ]
    
    # Get approver name if approved
    approver_name = None
    if application.approver:
        approver_name = f"{application.approver.first_name} {application.approver.last_name}"
    
    return ApplicationFullDetails(
        application_id=application.id,
        application_date=application.application_date,
        status=application.status.value,
        crop_type=application.crop_type_rel.name,
        farm_size_hectares=float(application.farm_size_hectares),
        expected_yield_kg=float(application.expected_yield_kg),
        expected_revenue_mwk=float(application.expected_revenue_mwk),
        district_name=application.district_rel.name,
        prediction_details=prediction_details,
        farmer_profile=farmer_profile_detail,
        yield_history=yield_history,
        review_history=review_history,
        approved_amount_mwk=float(application.approved_amount_mwk) if application.approved_amount_mwk else None,
        approval_date=application.approval_date,
        approver_name=approver_name,
        override_reason=application.override_reason
    )

# Additional utility endpoints for loan officers
@router.get("/dashboard/stats")
def get_dashboard_stats(
    current_user: User = Depends(require_loan_officer),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for loan officers"""
    
    if not check_loan_officer_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    accessible_districts = get_accessible_districts(current_user, db)
    
    if not accessible_districts:
        return {
            "total_applications": 0,
            "pending_applications": 0,
            "approved_applications": 0,
            "rejected_applications": 0,
            "total_approved_amount": 0
        }
    
    # Base query for accessible applications
    base_query = db.query(LoanApplication).filter(
        LoanApplication.district_id.in_(accessible_districts)
    )
    
    # Get statistics
    total_applications = base_query.count()
    
    pending_applications = base_query.filter(
        LoanApplication.status.in_([
            ApplicationStatus.SUBMITTED, 
            ApplicationStatus.UNDER_REVIEW
        ])
    ).count()
    
    approved_applications = base_query.filter(
        LoanApplication.status == ApplicationStatus.APPROVED
    ).count()
    
    rejected_applications = base_query.filter(
        LoanApplication.status == ApplicationStatus.REJECTED
    ).count()
    
    # Calculate total approved amount
    approved_amount_result = base_query.filter(
        LoanApplication.status == ApplicationStatus.APPROVED,
        LoanApplication.approved_amount_mwk.isnot(None)
    ).with_entities(
        func.sum(LoanApplication.approved_amount_mwk)
    ).scalar()
    
    total_approved_amount = float(approved_amount_result) if approved_amount_result else 0
    
    return {
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "approved_applications": approved_applications,
        "rejected_applications": rejected_applications,
        "total_approved_amount": total_approved_amount
    }

@router.get("/districts")
def get_accessible_districts_list(
    current_user: User = Depends(require_loan_officer),
    db: Session = Depends(get_db)
):
    """Get list of districts accessible to the loan officer"""
    
    if not check_loan_officer_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    accessible_district_ids = get_accessible_districts(current_user, db)
    
    if not accessible_district_ids:
        return []
    
    districts = db.query(District).filter(
        District.id.in_(accessible_district_ids)
    ).all()
    
    return [
        {
            "id": district.id,
            "name": district.name,
            "code": district.code,
            "region": district.region
        }
        for district in districts
    ]

@router.get("/crop-types")
def get_crop_types(
    current_user: User = Depends(require_loan_officer),
    db: Session = Depends(get_db)
):
    """Get list of available crop types"""
    
    if not check_loan_officer_permissions(current_user):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    crop_types = db.query(CropType).all()
    
    return [
        {
            "id": crop_type.id,
            "name": crop_type.name,
            "code": crop_type.code,
            "description": crop_type.description
        }
        for crop_type in crop_types
    ]