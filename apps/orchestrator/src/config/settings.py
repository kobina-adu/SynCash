"""
Configuration settings for SyncCash Orchestrator Service
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "SyncCash Orchestrator"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(
        default="postgres://synccash:synccash@localhost:5432/synccash",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/orc", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # Payment Processing
    max_transaction_amount: float = Field(default=10000.0, env="MAX_TRANSACTION_AMOUNT")
    min_transaction_amount: float = Field(default=1.0, env="MIN_TRANSACTION_AMOUNT")
    transaction_timeout_seconds: int = Field(default=300, env="TRANSACTION_TIMEOUT_SECONDS")
    
    # Retry Configuration
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    retry_backoff_base: float = Field(default=2.0, env="RETRY_BACKOFF_BASE")
    retry_backoff_max: float = Field(default=60.0, env="RETRY_BACKOFF_MAX")
    
    # Provider Configuration
    mtn_api_url: str = Field(default="https://sandbox.momodeveloper.mtn.com", env="MTN_API_URL")
    mtn_api_key: str = Field(default="", env="MTN_API_KEY")
    mtn_api_secret: str = Field(default="", env="MTN_API_SECRET")
    
    airtel_api_url: str = Field(default="https://openapiuat.airtel.africa", env="AIRTEL_API_URL")
    airtel_api_key: str = Field(default="", env="AIRTEL_API_KEY")
    airtel_api_secret: str = Field(default="", env="AIRTEL_API_SECRET")
    
    vodafone_api_url: str = Field(default="https://api.vodafone.com.gh", env="VODAFONE_API_URL")
    vodafone_api_key: str = Field(default="", env="VODAFONE_API_KEY")
    vodafone_api_secret: str = Field(default="", env="VODAFONE_API_SECRET")
    
    # Fraud Detection
    fraud_detection_enabled: bool = Field(default=True, env="FRAUD_DETECTION_ENABLED")
    max_daily_transaction_amount: float = Field(default=50000.0, env="MAX_DAILY_TRANSACTION_AMOUNT")
    max_transactions_per_minute: int = Field(default=10, env="MAX_TRANSACTIONS_PER_MINUTE")
    suspicious_amount_threshold: float = Field(default=5000.0, env="SUSPICIOUS_AMOUNT_THRESHOLD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
