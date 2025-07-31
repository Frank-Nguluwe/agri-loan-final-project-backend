from fastapi import APIRouter, Depends, HTTPException, Query
from pytz import timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pytz import timezone
from app.config.database import get_db
from app.config.settings import settings
from app.models.db_models import (
    User, 
    UserRole,
    District,
    SystemSetting
)
from app.schemas.admin_schemas import (
    ModelPerformanceResponse,
    SystemSettingUpdate,
    UserCreate,
    UserResponse,
    UserDetailResponse,
    UserUpdate
)
from app.utils.auth_utils import generate_random_password, hash_password
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/model-performance", response_model=ModelPerformanceResponse)
async def get_model_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get model performance metrics
    
    Returns:
    - accuracy: Current model accuracy score
    - recent_predictions: List of recent predictions with actual outcomes
    - drift_metrics: Data drift detection metrics
    """
    # Verify user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can access model performance data")
    
    # TODO: Replace with actual model metrics from your monitoring system
    # This is placeholder data
    return {
        "accuracy": 0.87,
        "recent_predictions": [
            {"predicted": 150000, "actual": 142000, "date": "2023-05-01"},
            {"predicted": 180000, "actual": 175000, "date": "2023-05-02"},
            {"predicted": 210000, "actual": 225000, "date": "2023-05-03"}
        ],
        "drift_metrics": {
            "feature_drift": {
                "farm_size": 0.12,
                "expected_yield": 0.08
            },
            "prediction_drift": 0.15
        }
    }

@router.post("/system-settings", response_model=dict)
async def update_system_setting(
    setting_data: SystemSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update system settings
    
    Required fields:
    - key: Setting key/name
    - value: New setting value
    - description: Description of the setting (optional)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update system settings")
    
    # Check if setting exists
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == setting_data.key
    ).first()
    
    if setting:
        # Update existing setting
        setting.value = setting_data.value
        if setting_data.description:
            setting.description = setting_data.description
        setting.last_updated = datetime.now(timezone(settings.TIMEZONE))
        setting.updated_by = current_user.id
    else:
        # Create new setting
        setting = SystemSetting(
            key=setting_data.key,
            value=setting_data.value,
            description=setting_data.description or "",
            last_updated=datetime.now(timezone(settings.TIMEZONE)),
            updated_by=current_user.id
        )
        db.add(setting)
    
    db.commit()
    
    return {"message": f"Setting '{setting_data.key}' updated successfully"}

@router.post("/users", response_model=UserDetailResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new user (Farmer, Loan Officer, Supervisor, or Admin)
    
    Required fields:
    - first_name
    - last_name
    - role
    - phone_number (for farmers)
    - district_id (for loan officers/supervisors)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    # Validate role
    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user role")
    
    # Validate required fields based on role
    if role == UserRole.FARMER and not user_data.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required for farmers")
    
    if role in [UserRole.LOAN_OFFICER, UserRole.SUPERVISOR] and not user_data.district_id:
        raise HTTPException(status_code=400, detail="District ID is required for loan officers and supervisors")
    
    # Check if district exists (for officers/supervisors)
    if user_data.district_id:
        district = db.query(District).filter(District.id == user_data.district_id).first()
        if not district:
            raise HTTPException(status_code=400, detail="Invalid district ID")
    
    # Check for existing user with same email or phone
    if user_data.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    if user_data.phone_number:
        existing_user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Phone number already in use")
    
    # Generate password if not provided
    password = user_data.password or generate_random_password()
    
    # Create user
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hash_password(password),
        role=role,
        district_id=user_data.district_id,
        is_active=True,
        created_at=datetime.now(timezone(settings.TIMEZONE))
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # TODO: Send welcome email with credentials if password was auto-generated
    
    return {
        "user_id": str(new_user.id),
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "email": new_user.email,
        "phone_number": new_user.phone_number,
        "role": new_user.role.value,
        "district_id": str(new_user.district_id) if new_user.district_id else None,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at
    }

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = Query(None),
    district_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users with optional filters
    
    Query Parameters:
    - role: Filter by user role
    - district_id: Filter by district (for loan officers/supervisors)
    - is_active: Filter by active/inactive status
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can list users")
    
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if district_id:
        query = query.filter(User.district_id == district_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.created_at.desc()).all()
    
    return [{
        "user_id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "district": user.district_rel.name if user.district_rel else None,
        "is_active": user.is_active
    } for user in users]

@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get details of a specific user
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view user details")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role.value,
        "district_id": str(user.district_id) if user.district_id else None,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

@router.put("/users/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user details
    
    All fields are optional - only provided fields will be updated
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update users")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.email is not None:
        # Check if email is already in use by another user
        if user_data.email != user.email:
            existing = db.query(User).filter(User.email == user_data.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_data.email
    if user_data.phone_number is not None:
        # Check if phone is already in use by another user
        if user_data.phone_number != user.phone_number:
            existing = db.query(User).filter(User.phone_number == user_data.phone_number).first()
            if existing:
                raise HTTPException(status_code=400, detail="Phone number already in use")
        user.phone_number = user_data.phone_number
    if user_data.district_id is not None:
        if user.role in [UserRole.LOAN_OFFICER, UserRole.SUPERVISOR]:
            # Verify district exists
            district = db.query(District).filter(District.id == user_data.district_id).first()
            if not district:
                raise HTTPException(status_code=400, detail="Invalid district ID")
            user.district_id = user_data.district_id
        else:
            user.district_id = None
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return {
        "user_id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role.value,
        "district_id": str(user.district_id) if user.district_id else None,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

@router.delete("/users/{user_id}", response_model=dict)
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Deactivate a user (sets is_active=False)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can deactivate users")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is already inactive")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}