"""
Application settings and configuration management.

This module provides centralized configuration using Pydantic for validation,
environment variable handling, and type safety.
"""

import os
from typing import List, Optional, Dict, Any
from functools import lru_cache

from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="postgresql://user:password@localhost:5432/reddit_analyzer")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    echo: bool = Field(default=False)
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://localhost:6379/0")
    password: Optional[str] = Field(default=None)
    max_connections: int = Field(default=10, ge=1, le=100)
    
    class Config:
        env_prefix = "REDIS_"


class APISettings(BaseSettings):
    """API configuration settings."""
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    reload: bool = Field(default=True)
    
    class Config:
        env_prefix = "API_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_secret_key: str = Field(default="your-jwt-secret-key")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)
    
    class Config:
        env_prefix = ""


class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    
    origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])
    credentials: bool = Field(default=True)
    methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    headers: List[str] = Field(default=["*"])
    
    @validator('origins', pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON string format
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v
    
    class Config:
        env_prefix = "CORS_"


class ExternalAPISettings(BaseSettings):
    """External API configuration settings."""
    
    openai_api_key: str = Field(default="")
    apify_api_key: str = Field(default="")
    google_sheets_credentials_path: str = Field(default="./config/google_credentials.json")
    
    class Config:
        env_prefix = ""


class SupabaseSettings(BaseSettings):
    """Supabase configuration settings."""
    
    url: str = Field(default="", description="Supabase project URL")
    key: str = Field(default="", description="Supabase anon key")
    service_role_key: str = Field(default="", description="Supabase service role key")
    brands_table: str = Field(default="brands", description="Table name for brands")
    results_table: str = Field(default="analysis_results", description="Table name for results")
    
    class Config:
        env_prefix = "SUPABASE_"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""
    
    requests_per_minute: int = Field(default=60, ge=1, le=1000)
    burst: int = Field(default=10, ge=1, le=100)
    
    class Config:
        env_prefix = "RATE_LIMIT_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    
    prometheus_port: int = Field(default=9090, ge=1, le=65535)
    jaeger_endpoint: str = Field(default="http://localhost:14268/api/traces")
    sentry_dsn: Optional[str] = Field(default=None)
    
    class Config:
        env_prefix = ""


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file_path: Optional[str] = Field(default=None)
    max_file_size: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)
    
    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality."""
    
    enable_caching: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=True)
    enable_rate_limiting: bool = Field(default=True)
    mock_external_apis: bool = Field(default=False)
    
    class Config:
        env_prefix = "ENABLE_"


class FileStorageSettings(BaseSettings):
    """File storage configuration settings."""
    
    upload_dir: str = Field(default="./uploads")
    max_file_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: List[str] = Field(default=[".txt", ".csv", ".json"])
    
    class Config:
        env_prefix = ""


class EmailSettings(BaseSettings):
    """Email configuration settings."""
    
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    use_tls: bool = Field(default=True)
    
    class Config:
        env_prefix = "SMTP_"


class Settings(PydanticBaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    api: APISettings = Field(default_factory=APISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    external_apis: ExternalAPISettings = Field(default_factory=ExternalAPISettings)
    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    file_storage: FileStorageSettings = Field(default_factory=FileStorageSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    
    # Convenience properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment.lower() == "testing"
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['development', 'production', 'testing', 'staging']
        if v.lower() not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns:
        Settings instance with all configuration loaded
    """
    return Settings()


# Convenience functions for accessing specific settings
def get_database_settings() -> DatabaseSettings:
    """Get database settings."""
    return get_settings().database


def get_redis_settings() -> RedisSettings:
    """Get Redis settings."""
    return get_settings().redis


def get_api_settings() -> APISettings:
    """Get API settings."""
    return get_settings().api


def get_security_settings() -> SecuritySettings:
    """Get security settings."""
    return get_settings().security


def get_cors_settings() -> CORSSettings:
    """Get CORS settings."""
    return get_settings().cors


def get_external_api_settings() -> ExternalAPISettings:
    """Get external API settings."""
    return get_settings().external_apis


def get_supabase_settings() -> SupabaseSettings:
    """Get Supabase settings."""
    return get_settings().supabase


def get_rate_limit_settings() -> RateLimitSettings:
    """Get rate limit settings."""
    return get_settings().rate_limit


def get_monitoring_settings() -> MonitoringSettings:
    """Get monitoring settings."""
    return get_settings().monitoring


def get_logging_settings() -> LoggingSettings:
    """Get logging settings."""
    return get_settings().logging


def get_feature_flags() -> FeatureFlags:
    """Get feature flags."""
    return get_settings().features


def get_file_storage_settings() -> FileStorageSettings:
    """Get file storage settings."""
    return get_settings().file_storage


def get_email_settings() -> EmailSettings:
    """Get email settings."""
    return get_settings().email


# Environment-specific configuration overrides
def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration overrides.
    
    Returns:
        Dictionary of environment-specific settings
    """
    settings = get_settings()
    
    if settings.is_production:
        return {
            "debug": False,
            "logging": {"level": "WARNING"},
            "api": {"workers": 8, "reload": False},
            "database": {"pool_size": 20, "max_overflow": 40},
            "features": {"mock_external_apis": False}
        }
    elif settings.is_testing:
        return {
            "debug": True,
            "logging": {"level": "DEBUG"},
            "database": {"url": "sqlite:///test.db"},
            "features": {"mock_external_apis": True}
        }
    else:  # development
        return {
            "debug": True,
            "logging": {"level": "INFO"},
            "features": {"mock_external_apis": False}
        }
