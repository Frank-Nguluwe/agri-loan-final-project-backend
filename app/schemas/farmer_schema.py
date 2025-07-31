# Pydantic models for request/response
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoanApplicationCreate(BaseModel):
    loan_farm_size: float = Field(..., gt=0, description="Farm size in hectares")
    loan_crop: str = Field(..., description="Crop type name or code")
    past_yield_kgs: Optional[float] = Field(None, description="Past yield in kg")
    past_yield_mk: Optional[float] = Field(None, description="Past revenue in MWK")
    expected_yield_kgs: float = Field(..., gt=0, description="Expected yield in kg")
    expected_yield_mk: float = Field(..., gt=0, description="Expected revenue in MWK")
    
class LoanApplicationResponse(BaseModel):
    application_id: UUID
    predicted_amount_mwk: Optional[float]
    prediction_confidence: Optional[float]
    status: str
    application_date: datetime
    
class LoanApplicationSummary(BaseModel):
    application_id: UUID
    application_date: datetime
    status: str
    crop_type: str
    predicted_amount_mwk: Optional[float]
    approved_amount_mwk: Optional[float]
    farm_size_hectares: float

class ApplicationReviewDetail(BaseModel):
    reviewer_name: str
    review_date: datetime
    comments: Optional[str]
    action: str

class LoanApplicationDetail(BaseModel):
    application_id: UUID
    application_date: datetime
    status: str
    crop_type: str
    farm_size_hectares: float
    expected_yield_kg: float
    expected_revenue_mwk: float
    district_name: str
    predicted_amount_mwk: Optional[float]
    prediction_confidence: Optional[float]
    prediction_date: Optional[datetime]
    approved_amount_mwk: Optional[float]
    approval_date: Optional[datetime]
    approver_name: Optional[str]
    override_reason: Optional[str]
    review_history: List[ApplicationReviewDetail]