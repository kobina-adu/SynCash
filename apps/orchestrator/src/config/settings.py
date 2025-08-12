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
        default="postgresql+asyncpg://postgres:password@localhost:5432/synccash_orchestrator",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
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
    MTN_MOMO_SUBSCRIPTION_KEY: str = Field(default="", env="MTN_MOMO_SUBSCRIPTION_KEY")
    MTN_MOMO_USER_ID: str = Field(default="", env="MTN_MOMO_USER_ID")
    MTN_MOMO_API_KEY: str = Field(default="", env="MTN_MOMO_API_KEY")
    MTN_MOMO_COLLECTION_USER_ID: str = Field(default="", env="MTN_MOMO_COLLECTION_USER_ID")
    MTN_MOMO_DISBURSEMENT_USER_ID: str = Field(default="", env="MTN_MOMO_DISBURSEMENT_USER_ID")
    
    AIRTELTIGO_CLIENT_ID: str = Field(default="", env="AIRTELTIGO_CLIENT_ID")
    AIRTELTIGO_CLIENT_SECRET: str = Field(default="", env="AIRTELTIGO_CLIENT_SECRET")
    AIRTELTIGO_MERCHANT_ID: str = Field(default="", env="AIRTELTIGO_MERCHANT_ID")
    AIRTELTIGO_API_KEY: str = Field(default="", env="AIRTELTIGO_API_KEY")
    
    VODAFONE_MERCHANT_ID: str = Field(default="", env="VODAFONE_MERCHANT_ID")
    VODAFONE_API_USERNAME: str = Field(default="", env="VODAFONE_API_USERNAME")
    VODAFONE_API_PASSWORD: str = Field(default="", env="VODAFONE_API_PASSWORD")
    VODAFONE_API_KEY: str = Field(default="", env="VODAFONE_API_KEY")
    VODAFONE_SECRET_KEY: str = Field(default="", env="VODAFONE_SECRET_KEY")
    vodafone_api_secret: str = Field(default="", env="VODAFONE_API_SECRET")
    
    # Provider sandbox mode
    PROVIDERS_SANDBOX_MODE: bool = Field(default=True, env="PROVIDERS_SANDBOX_MODE")
    
    # External Services
    fraud_detection_service_url: str = Field(default="http://localhost:8001", env="FRAUD_DETECTION_SERVICE_URL")
    fraud_detection_timeout: int = Field(default=5, env="FRAUD_DETECTION_TIMEOUT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_provider_configs(self) -> dict:
        """Get provider configurations for initialization"""
        return {
            "mtn_momo": {
                "subscription_key": self.MTN_MOMO_SUBSCRIPTION_KEY,
                "user_id": self.MTN_MOMO_USER_ID,
                "api_key": self.MTN_MOMO_API_KEY,
                "collection_user_id": self.MTN_MOMO_COLLECTION_USER_ID,
                "disbursement_user_id": self.MTN_MOMO_DISBURSEMENT_USER_ID,
                "sandbox": self.PROVIDERS_SANDBOX_MODE
            },
            "airteltigo_money": {
                "client_id": self.AIRTELTIGO_CLIENT_ID,
                "client_secret": self.AIRTELTIGO_CLIENT_SECRET,
                "merchant_id": self.AIRTELTIGO_MERCHANT_ID,
                "api_key": self.AIRTELTIGO_API_KEY,
                "sandbox": self.PROVIDERS_SANDBOX_MODE
            },
            "vodafone_cash": {
                "merchant_id": self.VODAFONE_MERCHANT_ID,
                "api_username": self.VODAFONE_API_USERNAME,
                "api_password": self.VODAFONE_API_PASSWORD,
                "api_key": self.VODAFONE_API_KEY,
                "secret_key": self.VODAFONE_SECRET_KEY,
                "sandbox": self.PROVIDERS_SANDBOX_MODE
            }
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
