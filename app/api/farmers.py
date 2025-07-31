from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pytz import timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List
from app.config.database import get_db
from app.config.settings import settings
from app.models.db_models import (
    User, FarmerProfile, LoanApplication, ApplicationReview, 
    CropType, District, YieldHistory, UserRole, ApplicationStatus
)
from app.schemas.farmer_schema import ApplicationReviewDetail, LoanApplicationCreate, LoanApplicationDetail, LoanApplicationResponse, LoanApplicationSummary
from app.utils.dependencies import require_farmer
from app.utils.farmers_utils import ensure_farmer_profile, get_crop_type_by_name_or_code
from app.services.ml_model import model_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.post("/applications", response_model=LoanApplicationResponse)
def submit_loan_application(
    application_data: LoanApplicationCreate,
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Submit a new loan application with real-time prediction"""
    try:
        # Ensure farmer has a profile
        farmer_profile = ensure_farmer_profile(db, current_user)
        
        # Get crop type
        crop_type = get_crop_type_by_name_or_code(db, application_data.loan_crop)
        
        # Determine district
        district_id = current_user.district_id
        if not district_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="District ID is required"
            )
        
        # Verify district exists
        district = db.query(District).filter(District.id == district_id).first()
        if not district:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="District not found"
            )
        
        # Prepare prediction input
        prediction_input = {
            'loan_farm_size': application_data.loan_farm_size,
            'loan_crop': crop_type.name.lower(),
            'past_yield_kgs': application_data.past_yield_kgs or 0.0,
            'past_yield_mk': application_data.past_yield_mk or 0.0,
            'expected_yield_kgs': application_data.expected_yield_kgs,
            'expected_yield_mk': application_data.expected_yield_mk
        }
        
        # Get real-time prediction
        try:
            prediction_result = model_service.predict(prediction_input)
            predicted_amount = prediction_result["predicted_amount_mwk"]
            confidence = prediction_result["prediction_confidence"]
        except Exception as e:
            logger.error(f"Prediction failed, using fallback: {str(e)}")
            predicted_amount = min(application_data.expected_yield_mk * 0.5, 300000)
            confidence = 0.5
        
        # Create and save loan application
        loan_application = LoanApplication(
            farmer_id=current_user.id,
            crop_type_id=crop_type.id,
            farm_size_hectares=application_data.loan_farm_size,
            expected_yield_kg=application_data.expected_yield_kgs,
            expected_revenue_mwk=application_data.expected_yield_mk,
            district_id=district_id,
            predicted_amount_mwk=predicted_amount,
            prediction_confidence=confidence,
            prediction_date=datetime.now(),
            status=ApplicationStatus.SUBMITTED
        )
        
        db.add(loan_application)
        db.commit()
        db.refresh(loan_application)
        
        # Save past yield data to YieldHistory if provided
        if application_data.past_yield_kgs is not None and application_data.past_yield_mk is not None:
            try:
                yield_history = YieldHistory(
                    farmer_id=farmer_profile.id,
                    year=datetime.now().year - 1,  # Previous year
                    crop_type_id=crop_type.id,
                    yield_amount_kg=application_data.past_yield_kgs,
                    revenue_mwk=application_data.past_yield_mk
                )
                db.add(yield_history)
                db.commit()
                db.refresh(yield_history)
                logger.info(f"Successfully saved yield history: {yield_history.id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save yield history: {str(e)}")
                # Continue with application even if yield history fails
        
        # Update farmer profile farm size if needed
        if farmer_profile.farm_size_hectares != application_data.loan_farm_size:
            farmer_profile.farm_size_hectares = application_data.loan_farm_size
            db.commit()
        
        return LoanApplicationResponse(
            application_id=loan_application.id,
            predicted_amount_mwk=predicted_amount,
            prediction_confidence=confidence,
            status=loan_application.status.value,
            application_date=loan_application.application_date
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application"
        )



@router.get("/applications", response_model=List[LoanApplicationSummary])
def get_farmer_applications(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get farmer's loan application history"""
    
    # Get applications with crop type information
    applications = db.query(LoanApplication).filter(
        LoanApplication.farmer_id == current_user.id
    ).join(
        CropType, LoanApplication.crop_type_id == CropType.id
    ).order_by(
        desc(LoanApplication.application_date)
    ).offset(offset).limit(limit).all()
    
    return [
        LoanApplicationSummary(
            application_id=app.id,
            application_date=app.application_date,
            status=app.status.value,
            crop_type=app.crop_type_rel.name,
            predicted_amount_mwk=float(app.predicted_amount_mwk) if app.predicted_amount_mwk else None,
            approved_amount_mwk=float(app.approved_amount_mwk) if app.approved_amount_mwk else None,
            farm_size_hectares=float(app.farm_size_hectares)
        )
        for app in applications
    ]

@router.get("/applications/{application_id}", response_model=LoanApplicationDetail)
def get_application_details(
    application_id: str,
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Get details of a specific application"""
    
    # Get application with all related data
    application = db.query(LoanApplication).filter(
        and_(
            LoanApplication.id == application_id,
            LoanApplication.farmer_id == current_user.id
        )
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get reviews
    reviews = db.query(ApplicationReview).filter(
        ApplicationReview.application_id == application.id
    ).join(
        User, ApplicationReview.reviewer_id == User.id
    ).order_by(ApplicationReview.review_date).all()
    
    review_history = [
        ApplicationReviewDetail(
            reviewer_name=f"{review.reviewer.first_name} {review.reviewer.last_name}",
            review_date=review.review_date,
            comments=review.comments,
            action=review.action.value
        )
        for review in reviews
    ]
    
    # Get approver name if approved
    approver_name = None
    if application.approved_by:
        approver = db.query(User).filter(User.id == application.approved_by).first()
        if approver:
            approver_name = f"{approver.first_name} {approver.last_name}"
    
    return LoanApplicationDetail(
        application_id=application.id,
        application_date=application.application_date,
        status=application.status.value,
        crop_type=application.crop_type_rel.name,
        farm_size_hectares=float(application.farm_size_hectares),
        expected_yield_kg=float(application.expected_yield_kg),
        expected_revenue_mwk=float(application.expected_revenue_mwk),
        district_name=application.district_rel.name,
        predicted_amount_mwk=float(application.predicted_amount_mwk) if application.predicted_amount_mwk else None,
        prediction_confidence=float(application.prediction_confidence) if application.prediction_confidence else None,
        prediction_date=application.prediction_date,
        approved_amount_mwk=float(application.approved_amount_mwk) if application.approved_amount_mwk else None,
        approval_date=application.approval_date,
        approver_name=approver_name,
        override_reason=application.override_reason,
        review_history=review_history
    )

# Additional utility endpoints
@router.get("/profile")
def get_farmer_profile(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Get farmer's profile information"""
    
    farmer_profile = ensure_farmer_profile(db, current_user)
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "district": current_user.district_rel.name if current_user.district_rel else None,
        "date_of_birth": farmer_profile.date_of_birth,
        "national_id": farmer_profile.national_id,
        "address": farmer_profile.address,
        "farm_location_gps": farmer_profile.farm_location_gps,
        "farm_size_hectares": float(farmer_profile.farm_size_hectares) if farmer_profile.farm_size_hectares else None,
    }

@router.get("/yield-history")
def get_yield_history(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Get farmer's historical yield data"""
    
    if not current_user.farmer_profile:
        return []
    
    yield_history = db.query(YieldHistory).filter(
        YieldHistory.farmer_id == current_user.farmer_profile.id
    ).join(
        CropType, YieldHistory.crop_type_id == CropType.id
    ).order_by(desc(YieldHistory.year)).all()
    
    return [
        {
            "year": history.year,
            "crop_type": history.crop_type_rel.name,
            "yield_amount_kg": float(history.yield_amount_kg) if history.yield_amount_kg else None,
            "revenue_mwk": float(history.revenue_mwk) if history.revenue_mwk else None,
        }
        for history in yield_history
    ]