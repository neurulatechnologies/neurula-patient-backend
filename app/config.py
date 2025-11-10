"""
Application configuration using Pydantic Settings
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Neurula Health API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./neurula_dev.db", description="Database connection string")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_OTP_DB: int = 1
    REDIS_SESSION_DB: int = 2

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="development-secret-key-please-change-in-production-min-32-characters", min_length=32, description="Secret key for JWT signing")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    AES_ENCRYPTION_KEY: str = Field(default="development-aes-encryption-key-32-chars-long-change-prod", min_length=32, description="AES encryption key")
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12

    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RESEND_COOLDOWN_SECONDS: int = 30

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    OTP_RATE_LIMIT_PER_HOUR: int = 5

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@neurula.health"
    SMTP_FROM_NAME: str = "Neurula Health"

    # SMS Configuration
    SMS_PROVIDER: str = "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # File Storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "neurula-files"
    S3_REGION: str = "us-east-1"

    # External APIs
    NABIDH_API_URL: str = "https://api.nabidh.ae/v1"
    NABIDH_API_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
            # Handle wildcard for development
            if "*" in origins:
                return ["*"]
            return origins
        return self.CORS_ORIGINS

    @property
    def redis_otp_url(self) -> str:
        """Get Redis URL for OTP database"""
        return self.REDIS_URL.rsplit("/", 1)[0] + f"/{self.REDIS_OTP_DB}"

    @property
    def redis_session_url(self) -> str:
        """Get Redis URL for session database"""
        return self.REDIS_URL.rsplit("/", 1)[0] + f"/{self.REDIS_SESSION_DB}"


# Global settings instance
settings = Settings()
