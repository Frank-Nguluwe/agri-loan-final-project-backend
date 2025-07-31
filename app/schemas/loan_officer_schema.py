# Pydantic models for response
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class ApplicationListItem(BaseModel):
    application_id: UUID
    farmer_name: str
    application_date: datetime
    predicted_amount_mwk: Optional[float]
    status: str
    crop_type: str
    farm_size_hectares: float
    district_name: str
    expected_yield_kg: float
    expected_revenue_mwk: float

class FarmerProfileDetail(BaseModel):
    user_id: UUID
    email: Optional[str]
    phone_number: Optional[str]
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime]
    national_id: Optional[str]
    address: Optional[str]
    farm_location_gps: Optional[str]
    farm_size_hectares: Optional[float]
    registration_date: datetime
    district_name: Optional[str]

class YieldHistoryItem(BaseModel):
    year: int
    crop_type: str
    yield_amount_kg: Optional[float]
    revenue_mwk: Optional[float]

class PredictionDetails(BaseModel):
    predicted_amount_mwk: Optional[float]
    prediction_confidence: Optional[float]
    prediction_date: Optional[datetime]
    model_version: Optional[str] = "v1.0" 

class ApplicationReviewHistory(BaseModel):
    reviewer_name: str
    review_date: datetime
    comments: Optional[str]
    action: str

class ApplicationFullDetails(BaseModel):
    # Application basic info
    application_id: UUID
    application_date: datetime
    status: str
    
    # Crop and farming details
    crop_type: str
    farm_size_hectares: float
    expected_yield_kg: float
    expected_revenue_mwk: float
    district_name: str
    
    # Prediction details
    prediction_details: PredictionDetails
    
    # Farmer profile
    farmer_profile: FarmerProfileDetail
    
    # Historical data
    yield_history: List[YieldHistoryItem]
    
    # Review history
    review_history: List[ApplicationReviewHistory]
    
    # Approval details (if any)
    approved_amount_mwk: Optional[float]
    approval_date: Optional[datetime]
    approver_name: Optional[str]
    override_reason: Optional[str]
