from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class ModelPerformanceResponse(BaseModel):
    accuracy: float
    recent_predictions: List[Dict[str, Any]]
    drift_metrics: Dict[str, Any]

class SystemSettingUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class UserRole(str, Enum):
    FARMER = "farmer"
    LOAN_OFFICER = "loan_officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole
    district_id: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    role: str
    district: Optional[str] = None
    is_active: bool

class UserDetailResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: str
    district_id: Optional[str] = None
    is_active: bool
    created_at: datetime

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    district_id: Optional[str] = None
    is_active: Optional[bool] = None