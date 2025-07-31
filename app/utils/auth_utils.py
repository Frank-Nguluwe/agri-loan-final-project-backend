import random
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Union
from pytz import timezone
from app.config.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_otp():
    return str(random.randint(100000, 999999))

def otp_expiry():
    return datetime.now(timezone('Africa/Blantyre')) + timedelta(minutes=10)


import secrets
import string

def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password with specified length.
    
    The password will contain:
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    - The remaining characters will be a mix of all character types
    
    Args:
        length: Length of the password to generate (default: 12)
        
    Returns:
        A securely generated random password
    """
    if length < 8:
        raise ValueError("Password length must be at least 8 characters")
    
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*()-_=+"
    
    # Ensure we have at least one character from each set
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest with random choices from all character sets
    all_chars = uppercase + lowercase + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the list to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)
