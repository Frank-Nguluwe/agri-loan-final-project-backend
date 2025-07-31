from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date
from uuid import UUID

class FarmerProfileUpdate(BaseModel):
    national_id: Optional[str]
    address: Optional[str]
    farm_location_gps: Optional[str]
    farm_size_hectares: Optional[float]
    date_of_birth: Optional[date]
    district_id: Optional[UUID] = None

class UserProfileUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    email: Optional[EmailStr]
    farmer_profile: Optional[FarmerProfileUpdate]
