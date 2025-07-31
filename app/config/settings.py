from pydantic_settings import BaseSettings
import os
from pytz import timezone
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_NAME: str = os.getenv("DATABASE_NAME") or 'agri_loan'
    DATABASE_USER: str = os.getenv("DATABASE_USER") or 'user'
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD") or 'password'
    SUPABASE_PASSWORD: str = os.getenv("SUPABASE_PASSWORD") or 'SUPABASE_PASSWORD'
    DATABASE_HOST: str = os.getenv("DATABASE_HOST") or 'localhost'
    DATABASE_PORT: int = os.getenv("DATABASE_PORT") or 5432
    DATABASE_URL: str = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}" or f"postgresql://postgres.vsjosscremuhlppalima"
    DATABASE_URL_SYNC: str = f"postgresql://postgres.vsjosscremuhlppalima:35WCM!Nf_iike#P@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    SECRET_KEY: str = os.getenv("SECRET_KEY") or 'your-secret-key'
    ALGORITHM: str = os.getenv("ALGORITHM") or 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS") or 7
    SUPABASE_URL: str = os.getenv("SUPABASE_URL") or f"postgresql://postgres.vsjosscremuhlppalima:{SUPABASE_PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" or 'https://your-supabase-url.supabase.co'


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
