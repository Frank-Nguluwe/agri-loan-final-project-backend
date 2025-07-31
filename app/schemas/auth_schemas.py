from pydantic import BaseModel, EmailStr, Field
from app.models.db_models import UserRole
from typing import Optional
from uuid import UUID
from enum import Enum

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
    
# class PasswordResetRequest(BaseModel):
#     email: Optional[EmailStr] = None
#     phone_number: Optional[str] = None
#     new_password: str
#     confirm_password: str
    
class PasswordResetRequest(BaseModel):
    identifier: str = Field(..., description="Phone number or email")

class VerifyOtpRequest(BaseModel):
    otp: str
    new_password: str
    
    

class SignupRoleEnum(str, Enum):
    farmer = "farmer"
    loan_officer = "loan_officer"
    supervisor = "supervisor"
    admin = "admin"

class SignupRequest(BaseModel):
    email: EmailStr
    phone_number: str
    first_name: str
    last_name: str
    password: str
    role: SignupRoleEnum
    district_id: Optional[UUID] = None

    
