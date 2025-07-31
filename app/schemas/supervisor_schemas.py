# Pydantic models for request/response
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator


class LoanOfficerStats(BaseModel):
    officer_id: str
    name: str
    active_applications: int
    total_applications: int
    approved_applications: int
    pending_applications: int
    avg_processing_time_days: Optional[float]
    district_name: str

class DashboardMetrics(BaseModel):
    total_applications: int
    approved_applications: int
    pending_applications: int
    rejected_applications: int
    total_amount_approved: float
    average_approval_amount: float
    approval_rate: float
    loan_officer_stats: List[LoanOfficerStats]
    monthly_trends: dict
    district_summary: dict

class LoanOfficerSummary(BaseModel):
    officer_id: str
    name: str
    email: Optional[str]
    phone_number: Optional[str]
    active_applications: int
    total_applications: int
    district_name: str
    is_active: bool
    assigned_date: Optional[datetime]

class ApplicationApprovalRequest(BaseModel):
    action: str = Field(..., description="'approve' or 'reject'")
    approved_amount_mwk: Optional[float] = Field(None, description="Approved amount (required for approval)")
    override_prediction: bool = Field(False, description="Whether to override ML prediction")
    override_reason: Optional[str] = Field(None, description="Reason for override (required if override_prediction=True)")
    comments: Optional[str] = Field(None, description="Additional comments")

    @field_validator('approved_amount_mwk')
    def validate_approved_amount(cls, v: Optional[float], info: ValidationInfo):
        if info.data.get('action') == 'approve' and (v is None or v <= 0):
            raise ValueError('approved_amount_mwk must be positive for approval')
        return v

    @field_validator('override_reason')
    def validate_override_reason(cls, v: Optional[str], info: ValidationInfo):
        if info.data.get('override_prediction') and not v:
            raise ValueError('override_reason is required when override_prediction is True')
        return v
class ApplicationApprovalResponse(BaseModel):
    message: str
    application_id: str
    new_status: str
    approved_amount: Optional[float]
    approval_date: Optional[datetime]