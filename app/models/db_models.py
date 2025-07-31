from enum import Enum
import uuid
from sqlalchemy import (
    UUID, Column, ForeignKey, Integer, String, Boolean, 
    DateTime, Enum as SQLEnum, Text, Numeric, func
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

## Enums for categorical data

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class MaritalStatusEnum(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widowed = "widowed"

class EducationLevelEnum(str, Enum):
    none = "none"
    primary = "primary"
    secondary = "secondary"
    tertiary = "tertiary"


class UserRole(str, Enum):
    FARMER = "farmer"
    LOAN_OFFICER = "loan_officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"


class ReviewAction(str, Enum):
    RECOMMEND_APPROVAL = "recommend_approval"
    REQUEST_CHANGES = "request_changes"
    REJECT = "reject"

## Reference Tables (Lookup Tables)
class District(Base):
    __tablename__ = "districts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    region = Column(String(100))
    
    # Relationships
    users = relationship("User", back_populates="district_rel")
    applications = relationship("LoanApplication", back_populates="district_rel")

class CropType(Base):
    __tablename__ = "crop_types"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    yield_history = relationship("YieldHistory", back_populates="crop_type_rel")
    applications = relationship("LoanApplication", back_populates="crop_type_rel")

## Core Tables
class User(Base):
    __tablename__ = "users"


    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    gender = Column(SQLEnum(GenderEnum), nullable=True)
    marital_status = Column(SQLEnum(MaritalStatusEnum), nullable=True)
    num_children = Column(Integer, nullable=True)
    disability_status = Column(Boolean, default=False)
    education_level = Column(SQLEnum(EducationLevelEnum), nullable=True)

    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    district_id = Column(UUID, ForeignKey("districts.id"), nullable=True)
    otp = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    # Relationships
    district_rel = relationship("District", back_populates="users")
    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    loan_applications = relationship("LoanApplication", back_populates="farmer", foreign_keys="LoanApplication.farmer_id")
    reviews = relationship("ApplicationReview", back_populates="reviewer")
    managed_loan_officers = relationship(
        "User",
        secondary="supervisor_loan_officer",
        primaryjoin="User.id==supervisor_loan_officer.c.supervisor_id",
        secondaryjoin="User.id==supervisor_loan_officer.c.loan_officer_id",
        backref="supervisors"
    )
    settings_updated = relationship("SystemSetting", back_populates="updated_by_rel")

    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        if phone_number and not phone_number.startswith('0'):
            raise ValueError("Phone number must start with 0")
        return phone_number
        

class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), unique=True)
    date_of_birth = Column(DateTime)
    national_id = Column(String(50), unique=True)
    address = Column(Text)
    farm_location_gps = Column(String(50))  # GPS coordinates
    farm_size_hectares = Column(Numeric(10, 2))
    is_new_applicant = Column(Boolean, default=True)

    
    # Relationships
    user = relationship("User", back_populates="farmer_profile")
    yield_history = relationship("YieldHistory", back_populates="farmer")

class YieldHistory(Base):
    __tablename__ = "yield_history"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    farmer_id = Column(UUID, ForeignKey("farmer_profiles.id"))
    year = Column(Integer, nullable=False)
    crop_type_id = Column(UUID, ForeignKey("crop_types.id"))
    yield_amount_kg = Column(Numeric(10, 2))
    revenue_mwk = Column(Numeric(12, 2))
    
    # Relationships
    farmer = relationship("FarmerProfile", back_populates="yield_history")
    crop_type_rel = relationship("CropType", back_populates="yield_history")

class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    farmer_id = Column(UUID, ForeignKey("users.id"))
    application_date = Column(DateTime, default=func.now())
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    crop_type_id = Column(UUID, ForeignKey("crop_types.id"))
    farm_size_hectares = Column(Numeric(10, 2))
    expected_yield_kg = Column(Numeric(10, 2))
    expected_revenue_mwk = Column(Numeric(12, 2))
    district_id = Column(UUID, ForeignKey("districts.id"))
    
    # Model prediction
    predicted_amount_mwk = Column(Numeric(12, 2))
    prediction_confidence = Column(Numeric(5, 2))
    prediction_date = Column(DateTime)
    
    # Final decision
    approved_amount_mwk = Column(Numeric(12, 2))
    approval_date = Column(DateTime)
    approved_by = Column(UUID, ForeignKey("users.id"))
    override_reason = Column(Text)
    
    # Relationships
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="loan_applications")
    crop_type_rel = relationship("CropType", back_populates="applications")
    district_rel = relationship("District", back_populates="applications")
    reviews = relationship("ApplicationReview", back_populates="application")
    approver = relationship("User", foreign_keys=[approved_by])

class ApplicationReview(Base):
    __tablename__ = "application_reviews"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    application_id = Column(UUID, ForeignKey("loan_applications.id"))
    reviewer_id = Column(UUID, ForeignKey("users.id"))
    review_date = Column(DateTime, default=func.now())
    comments = Column(Text)
    action = Column(SQLEnum(ReviewAction))
    
    # Relationships
    application = relationship("LoanApplication", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

## System Management Tables
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    last_updated = Column(DateTime, default=func.now())
    updated_by = Column(UUID, ForeignKey("users.id"))
    
    # Relationships
    updated_by_rel = relationship("User", back_populates="settings_updated")


## Association Tables
class SupervisorLoanOfficer(Base):
    __tablename__ = "supervisor_loan_officer"
    
    supervisor_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    loan_officer_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    assigned_date = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)