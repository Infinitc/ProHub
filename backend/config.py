"""
Configuration settings for ProHub
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # App Settings
    APP_NAME: str = "ProHub"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()
