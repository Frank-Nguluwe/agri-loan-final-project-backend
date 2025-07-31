from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.db_models import FarmerProfile, User
from app.schemas.auth_schemas import LoginRequest, PasswordResetRequest, SignupRequest, Token, VerifyOtpRequest
from app.schemas.base_response_schema import BaseResponse
from app.utils.auth_utils import generate_otp, hash_password, verify_password, create_access_token
from pytz import timezone


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    
    if login_data.email:
        user = db.query(User).filter(User.email == login_data.email).first()
    elif login_data.phone_number:
        user = db.query(User).filter(User.phone_number == login_data.phone_number).first()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login credentials")
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    data = {
        "user_id": str(user.id),
        "role": user.role,
        "full_name": f"{user.last_name.upper()} {user.first_name.title()}"
    }
    token = create_access_token(data=data)
    return Token(access_token=token, token_type="Bearer")



@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=BaseResponse)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):

    try:
        # Uniqueness checks
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        if db.query(User).filter(User.phone_number == user_data.phone_number).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already in use")

        # Create user
        new_user = User(
            email=user_data.email.lower(),
            phone_number=user_data.phone_number,
            first_name=user_data.first_name.title(),
            last_name=user_data.last_name.title(),
            role=user_data.role,
            hashed_password=hash_password(user_data.password),
            district_id=user_data.district_id
        )
        db.add(new_user)
        db.flush()  # Get new_user.id

        # Optionally create farmer profile
        if user_data.role == "farmer":
            farmer = FarmerProfile(user_id=new_user.id)
            db.add(farmer)

        db.commit()
        return BaseResponse(message="Signup successful", status_code=status.HTTP_201_CREATED, data={"user_id": new_user.id})
    except HTTPException as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during signup")
    


@router.post("/password-reset")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    identifier = request.identifier.lower()
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone_number == identifier)
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    otp = generate_otp()
    # user.otp = otp
    # user.otp_expires_at = otp_expiry()

    # db.commit()

    # Send OTP via SMS or Email (mock)
    print(f"DEBUG: OTP for {identifier} is {otp}")  # replace with actual email/SMS logic

    return {"message": "OTP sent to your registered contact method."}

@router.post("/verify-otp")
def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.otp == request.otp).first()

    if not user or not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone('Africa/Blantyre')):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.hashed_password = hash_password(request.new_password)
    user.otp = None
    user.otp_expires_at = None

    db.commit()
    return {"message": "Password has been reset successfully."}