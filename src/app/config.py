import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application configuration settings.

    All tunable application variables are defined here so they can be overridden
    via environment variables or a .env file without changing source code.
    """

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./yatra.db")

    # -------------------------------------------------------------------------
    # Security / JWT
    # -------------------------------------------------------------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # -------------------------------------------------------------------------
    # Google OAuth
    # Set ENABLE_GOOGLE_AUTH=true in production to require real Google tokens.
    # When False (default) a dev-login endpoint is available for testing.
    # -------------------------------------------------------------------------
    ENABLE_GOOGLE_AUTH: bool = os.getenv("ENABLE_GOOGLE_AUTH", "false").lower() == "true"
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # -------------------------------------------------------------------------
    # Email
    # Set EMAIL_LOG_ONLY=false (and provide SMTP_* vars) to actually send mail.
    # Default is True so tests/dev environments do not need a real mail server.
    # -------------------------------------------------------------------------
    EMAIL_LOG_ONLY: bool = os.getenv("EMAIL_LOG_ONLY", "true").lower() == "true"
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")

    # -------------------------------------------------------------------------
    # Request limits
    # Maximum number of *active* requests a seeker / volunteer may have at once.
    # -------------------------------------------------------------------------
    SEEKER_REQUEST_LIMIT: int = int(os.getenv("SEEKER_REQUEST_LIMIT", "5"))
    VOLUNTEER_REQUEST_LIMIT: int = int(os.getenv("VOLUNTEER_REQUEST_LIMIT", "5"))

    # -------------------------------------------------------------------------
    # Matching
    # A seeker and a volunteer are matched when they share the same route AND
    # either fly the same flight number OR their departure times are within
    # MATCH_TIME_BUFFER_HOURS of each other.
    # -------------------------------------------------------------------------
    MATCH_TIME_BUFFER_HOURS: int = int(os.getenv("MATCH_TIME_BUFFER_HOURS", "4"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
