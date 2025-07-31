from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class YieldInfo(BaseModel):
    year: int
    crop_type: str
    yield_amount_kg: float
    revenue_mwk: float

class FarmerProfileInfo(BaseModel):
    national_id: Optional[str]
    address: Optional[str]
    farm_location_gps: Optional[str]
    farm_size_hectares: Optional[float]
    yield_history: List[YieldInfo]

class DashboardUserInfo(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    district: Optional[str]
    farmer_profile: Optional[FarmerProfileInfo]


class CropTypeOut(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None

    class Config:
        from_attributes = True