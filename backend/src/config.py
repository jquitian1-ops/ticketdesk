"""Application configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql://ticketdesk_user:dev_password@localhost:5432/ticketdesk_dev"
    DATABASE_SSL: bool = False

    # API
    API_TITLE: str = "TicketDesk Enterprise API"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "AI-Powered Candidate Screening Platform"

    # Security
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
