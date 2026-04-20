"""
config.py - Environment variable loading using pydantic-settings

.env file se sare configs yahan centralize hain.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/iam_db"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    APP_NAME: str = "IAM Service"
    DEBUG: bool = False
    
    # IAM External API Key
    IAM_API_KEY: str = "default-insecure-api-key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
