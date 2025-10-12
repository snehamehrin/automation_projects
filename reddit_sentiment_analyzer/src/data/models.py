"""
Data models for the Reddit Sentiment Analyzer.

This module defines Pydantic models for all data structures used throughout
the application, ensuring type safety and validation.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class DataType(str, Enum):
    """Enumeration for Reddit data types."""
    POST = "post"
    COMMENT = "comment"


class SentimentType(str, Enum):
    """Enumeration for sentiment types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BrandData(BaseModel):
    """Model for brand information."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Brand name")
    category: Optional[str] = Field(None, max_length=255, description="Brand category/industry")
    company_url: Optional[str] = Field(None, description="Company website URL")
    
    @validator('company_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nike",
                "category": "Sportswear",
                "company_url": "https://www.nike.com"
            }
        }


class RedditPost(BaseModel):
    """Model for Reddit post/comment data."""
    
    id: str = Field(..., description="Unique identifier for the post/comment")
    text: str = Field(..., min_length=1, description="Post/comment text content")
    data_type: DataType = Field(..., description="Type of Reddit content")
    
    # Post-specific fields
    title: Optional[str] = Field(None, description="Post title (for posts only)")
    community: Optional[str] = Field(None, description="Subreddit name")
    up_votes: Optional[int] = Field(None, ge=0, description="Number of upvotes")
    down_votes: Optional[int] = Field(None, ge=0, description="Number of downvotes")
    
    # Comment-specific fields
    post_id: Optional[str] = Field(None, description="Parent post ID (for comments)")
    parent_id: Optional[str] = Field(None, description="Parent comment ID (for replies)")
    
    # Common fields
    author: Optional[str] = Field(None, description="Author username")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    url: Optional[str] = Field(None, description="Reddit URL")
    
    # Brand context
    brand_name: Optional[str] = Field(None, description="Associated brand name")
    company_url: Optional[str] = Field(None, description="Associated company URL")
    
    # Analysis fields
    sentiment: Optional[SentimentType] = Field(None, description="Detected sentiment")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Sentiment confidence score")
    themes: List[str] = Field(default_factory=list, description="Detected themes")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        return v.strip()
    
    @validator('created_at', pre=True)
    def parse_created_at(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "text": "I love this brand! Great quality and service.",
                "data_type": "post",
                "title": "Amazing experience with Brand X",
                "community": "r/reviews",
                "up_votes": 15,
                "author": "user123",
                "created_at": "2024-01-15T10:30:00Z",
                "url": "https://reddit.com/r/reviews/comments/abc123",
                "brand_name": "Brand X",
                "sentiment": "positive",
                "confidence": 0.95
            }
        }


class SentimentSummary(BaseModel):
    """Model for sentiment analysis summary."""
    
    positive: int = Field(0, ge=0, description="Number of positive posts")
    negative: int = Field(0, ge=0, description="Number of negative posts")
    neutral: int = Field(0, ge=0, description="Number of neutral posts")
    total: int = Field(0, ge=0, description="Total number of posts analyzed")
    
    @property
    def positive_percentage(self) -> float:
        """Calculate positive sentiment percentage."""
        return (self.positive / self.total * 100) if self.total > 0 else 0.0
    
    @property
    def negative_percentage(self) -> float:
        """Calculate negative sentiment percentage."""
        return (self.negative / self.total * 100) if self.total > 0 else 0.0
    
    @property
    def neutral_percentage(self) -> float:
        """Calculate neutral sentiment percentage."""
        return (self.neutral / self.total * 100) if self.total > 0 else 0.0
    
    @validator('total')
    def validate_total(cls, v, values):
        if v != sum([values.get('positive', 0), values.get('negative', 0), values.get('neutral', 0)]):
            raise ValueError("Total must equal sum of positive, negative, and neutral")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "positive": 45,
                "negative": 20,
                "neutral": 35,
                "total": 100
            }
        }


class AnalysisResult(BaseModel):
    """Model for complete analysis results."""
    
    # Brand information
    brand_name: str = Field(..., description="Brand name")
    brand_category: Optional[str] = Field(None, description="Brand category")
    company_url: Optional[str] = Field(None, description="Company URL")
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    total_posts: int = Field(0, ge=0, description="Total posts analyzed")
    
    # Sentiment analysis
    sentiment_summary: Dict[str, Union[int, float]] = Field(default_factory=dict, description="Sentiment summary")
    key_insight: str = Field("", description="Key behavioral insight")
    
    # Detailed analysis
    thematic_breakdown: List[str] = Field(default_factory=list, description="Thematic analysis breakdown")
    customer_segments: List[str] = Field(default_factory=list, description="Identified customer segments")
    strategic_recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    
    # Report generation
    html_report: str = Field("", description="Complete HTML report")
    
    # Raw data
    raw_data: List[RedditPost] = Field(default_factory=list, description="Raw Reddit posts used in analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "Nike",
                "brand_category": "Sportswear",
                "company_url": "https://www.nike.com",
                "analysis_timestamp": "2024-01-15T10:30:00Z",
                "total_posts": 150,
                "sentiment_summary": {
                    "positive": 60,
                    "negative": 25,
                    "neutral": 65,
                    "total": 150
                },
                "key_insight": "Nike faces a 'quality perception gap' - 40% of discussions mention durability concerns, particularly among long-term users seeking value for money.",
                "thematic_breakdown": [
                    "Quality and durability concerns",
                    "Price point discussions",
                    "Brand loyalty and community"
                ],
                "customer_segments": [
                    "Performance athletes seeking premium quality",
                    "Casual users prioritizing comfort and style",
                    "Value-conscious consumers comparing alternatives"
                ],
                "strategic_recommendations": [
                    "Address durability concerns through transparent quality communication",
                    "Develop mid-tier product line for value-conscious segment",
                    "Leverage community loyalty for advocacy programs"
                ]
            }
        }


class SearchQuery(BaseModel):
    """Model for search query parameters."""
    
    query: str = Field(..., min_length=1, description="Search query string")
    max_results: int = Field(50, ge=1, le=1000, description="Maximum results to return")
    country: str = Field("us", min_length=2, max_length=2, description="Country code")
    language: str = Field("en", min_length=2, max_length=5, description="Language code")
    date_limit: Optional[datetime] = Field(None, description="Date limit for search results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "site:reddit.com Nike sportswear review",
                "max_results": 50,
                "country": "us",
                "language": "en"
            }
        }


class ScrapingConfig(BaseModel):
    """Model for scraping configuration."""
    
    max_posts: int = Field(1, ge=1, le=100, description="Maximum posts per URL")
    max_comments: int = Field(20, ge=1, le=500, description="Maximum comments per post")
    max_communities: int = Field(1, ge=1, le=10, description="Maximum communities to scrape")
    scroll_timeout: int = Field(40, ge=10, le=300, description="Scroll timeout in seconds")
    use_proxy: bool = Field(True, description="Whether to use proxy for scraping")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_posts": 1,
                "max_comments": 20,
                "max_communities": 1,
                "scroll_timeout": 40,
                "use_proxy": True
            }
        }


class ProcessingConfig(BaseModel):
    """Model for data processing configuration."""
    
    max_text_length: int = Field(1200, ge=100, le=5000, description="Maximum text length per post")
    max_posts: int = Field(120, ge=10, le=1000, description="Maximum posts for analysis")
    min_text_length: int = Field(20, ge=1, le=100, description="Minimum text length to keep")
    remove_duplicates: bool = Field(True, description="Whether to remove duplicate posts")
    filter_bot_posts: bool = Field(True, description="Whether to filter bot posts")
    filter_deleted_posts: bool = Field(True, description="Whether to filter deleted posts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_text_length": 1200,
                "max_posts": 120,
                "min_text_length": 20,
                "remove_duplicates": True,
                "filter_bot_posts": True,
                "filter_deleted_posts": True
            }
        }


class APIResponse(BaseModel):
    """Model for API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field("", description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "data": {"brand_name": "Nike", "total_posts": 150},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class BatchAnalysisRequest(BaseModel):
    """Model for batch analysis requests."""
    
    brands: List[BrandData] = Field(..., min_items=1, description="List of brands to analyze")
    output_sheet_id: Optional[str] = Field(None, description="Output Google Sheet ID")
    processing_config: Optional[ProcessingConfig] = Field(None, description="Processing configuration")
    scraping_config: Optional[ScrapingConfig] = Field(None, description="Scraping configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brands": [
                    {"name": "Nike", "category": "Sportswear"},
                    {"name": "Adidas", "category": "Sportswear"}
                ],
                "output_sheet_id": "1fmseuHckPERoc5Pq5Wbnd_2lP4sZA-HRqXt3l9WJ2PA"
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Model for batch analysis responses."""
    
    total_brands: int = Field(..., description="Total number of brands requested")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    results: List[AnalysisResult] = Field(default_factory=list, description="Analysis results")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Error details")
    processing_time: float = Field(..., description="Total processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_brands": 2,
                "successful_analyses": 2,
                "failed_analyses": 0,
                "results": [],
                "errors": [],
                "processing_time": 45.2
            }
        }
