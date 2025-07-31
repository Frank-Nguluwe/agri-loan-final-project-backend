
# Helper functions
import logging
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.models.db_models import CropType, FarmerProfile, User, YieldHistory
from app.schemas.ml_schemas import LoanPredictionInput
from app.services.ml_model import ModelService
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_crop_type_by_name_or_code(db: Session, crop_identifier: str) -> CropType:
    """Get crop type by name or code"""
    crop_type = db.query(CropType).filter(
        (CropType.name == crop_identifier.title()) | (CropType.code == crop_identifier)
    ).first()
    if not crop_type:
        raise HTTPException(
            status_code=404,
            detail=f"Crop type '{crop_identifier}' not found"
        )
    return crop_type

def ensure_farmer_profile(db: Session, user: User) -> FarmerProfile:
    """Ensure farmer has a profile, create if doesn't exist"""
    if not user.farmer_profile:
        farmer_profile = FarmerProfile(
            user_id=user.id,
            farm_size_hectares=0.0  # Will be updated from application
        )
        db.add(farmer_profile)
        db.commit()
        db.refresh(farmer_profile)
        return farmer_profile
    return user.farmer_profile

# Initialize the model service
model_service = ModelService()

def calculate_loan_prediction(
    crop_type: str,
    farm_size: float,
    expected_yield: float,
    expected_revenue: float,
    past_yield: Optional[float],
    past_revenue: Optional[float]
) -> tuple[float, float]:
    """
    Simplified prediction function that only uses the 6 required features
    """
    try:
        # Use provided past yields or default to 0 if not available
        past_yield = past_yield if past_yield is not None else 0.0
        past_revenue = past_revenue if past_revenue is not None else 0.0
        
        # Prepare input data with exactly the 6 required features
        input_data = LoanPredictionInput(
            loan_farm_size=farm_size,
            loan_crop=crop_type,
            past_yield_kgs=past_yield,
            past_yield_mk=past_revenue,
            expected_yield_kgs=expected_yield,
            expected_yield_mk=expected_revenue
        )
        
        # Get prediction from model service
        prediction = model_service.predict(input_data)
        
        # Calculate confidence score (simplified version)
        confidence = 0.7  # Base confidence
        if past_yield > 0 and past_revenue > 0:
            confidence = min(0.9, confidence + 0.2)  # Higher confidence if historical data exists
        
        return prediction, confidence
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Loan prediction failed: {str(e)}")
        # Fallback to simple calculation if model fails
        base_amount = min(expected_revenue * 0.5, 300000)
        return float(base_amount), 0.5  # Low confidence for fallback