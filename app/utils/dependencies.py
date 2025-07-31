from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.db_models import User
from app.config.settings import settings

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user

def require_loan_officer(user: User = Depends(get_current_user)) -> User:
    if user.role != "loan_officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Loan officer role required")
    return user

def require_supervisor(user: User = Depends(get_current_user)) -> User:
    if user.role != "supervisor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor role required")
    return user

def require_farmer(user: User = Depends(get_current_user)) -> User:
    if user.role != "farmer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer role required")
    return user