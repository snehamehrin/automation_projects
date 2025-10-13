"""
Configuration management - loads from .env
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Apify
    APIFY_API_KEY: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Optional settings
    MAX_REDDIT_URLS: int = 10
    MAX_POSTS_PER_URL: int = 20
    MAX_COMMENTS_PER_POST: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
