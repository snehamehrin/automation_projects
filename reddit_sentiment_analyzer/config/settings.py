"""
Configuration management - loads from .env
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    SUPABASE_URL: str = "https://dummy.supabase.co"
    SUPABASE_KEY: str = "dummy-key"
    
    # Apify
    APIFY_API_KEY: str = "dummy-token"
    
    # OpenAI
    OPENAI_API_KEY: str = "dummy-key"
    
    # Optional settings
    MAX_REDDIT_URLS: int = 10
    MAX_POSTS_PER_URL: int = 20
    MAX_COMMENTS_PER_POST: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    return Settings()
