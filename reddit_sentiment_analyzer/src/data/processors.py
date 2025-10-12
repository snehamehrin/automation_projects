"""
Data processing and filtering for Reddit posts.

This module implements the data processing pipeline that filters, normalizes,
and prepares Reddit data for sentiment analysis.
"""

import asyncio
import logging
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
import re

from .models import RedditPost, BrandData, ProcessingConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """
    Data processor for Reddit posts and comments.
    
    Implements the filtering, normalization, and deduplication pipeline
    that prepares Reddit data for sentiment analysis.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize the data processor."""
        self.config = config or ProcessingConfig()
        self._initialized = False
        
        # Filter patterns for different types of content
        self.filter_patterns = {
            'bot': [
                "i am a bot",
                "action was performed automatically",
                "contact the moderators",
                "automoderator",
                "bot, and this action",
                "performed automatically",
                "/message/compose/?to=",
                "if you have any questions or concerns"
            ],
            'deleted': [
                "[deleted]",
                "[removed]",
                "deleted by user",
                "removed by moderator"
            ],
            'moderator': [
                "#### about participation",
                "discussion in this subreddit",
                "please vote accordingly",
                "removal or ban territory",
                "good - it is grounded in science",
                "bad - it utilizes generalizations",
                "rooted in science rather than",
                "peer reviewed sources",
                "off topic discussion",
                "please [contact the moderators"
            ],
            'welcome': [
                "welcome to",
                "welcome to the",
                "thanks for joining",
                "new to the sub",
                "first time posting",
                "glad you're here"
            ],
            'spam': [
                "check out my",
                "follow me on",
                "link in bio",
                "dm me for",
                "click here",
                "subscribe to my"
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the data processor."""
        if self._initialized:
            return
        
        logger.info("Initializing data processor")
        self._initialized = True
        logger.info("Data processor initialized successfully")
    
    async def process_posts(
        self, 
        posts: List[RedditPost], 
        brand_data: Optional[BrandData] = None
    ) -> List[RedditPost]:
        """
        Process a list of Reddit posts through the filtering pipeline.
        
        Args:
            posts: List of Reddit posts to process
            brand_data: Optional brand data for context
            
        Returns:
            List of processed and filtered posts
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Processing {len(posts)} posts")
        
        # Step 1: Basic validation and cleaning
        validated_posts = await self._validate_posts(posts)
        logger.debug(f"Validated {len(validated_posts)} posts")
        
        # Step 2: Apply content filters
        filtered_posts = await self._filter_content(validated_posts)
        logger.debug(f"Filtered to {len(filtered_posts)} posts")
        
        # Step 3: Normalize data format
        normalized_posts = await self._normalize_posts(filtered_posts)
        logger.debug(f"Normalized {len(normalized_posts)} posts")
        
        # Step 4: Remove duplicates
        deduplicated_posts = await self._deduplicate_posts(normalized_posts)
        logger.debug(f"Deduplicated to {len(deduplicated_posts)} posts")
        
        # Step 5: Apply length and count limits
        final_posts = await self._apply_limits(deduplicated_posts)
        logger.info(f"Final processed posts: {len(final_posts)}")
        
        return final_posts
    
    async def _validate_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Validate posts and remove invalid ones."""
        validated = []
        
        for post in posts:
            try:
                # Check if post has required fields
                if not post.id or not post.text:
                    continue
                
                # Check minimum text length
                if len(post.text.strip()) < self.config.min_text_length:
                    continue
                
                # Check if text is not just whitespace
                if not post.text.strip():
                    continue
                
                validated.append(post)
                
            except Exception as e:
                logger.warning(f"Error validating post {post.id}: {e}")
                continue
        
        return validated
    
    async def _filter_content(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Filter out unwanted content based on patterns."""
        if not self.config.filter_bot_posts and not self.config.filter_deleted_posts:
            return posts
        
        filtered = []
        
        for post in posts:
            try:
                # Combine title and text for filtering
                combined_text = f"{post.title or ''} {post.text}".lower()
                
                # Check for bot patterns
                if self.config.filter_bot_posts:
                    if any(pattern in combined_text for pattern in self.filter_patterns['bot']):
                        continue
                
                # Check for deleted content
                if self.config.filter_deleted_posts:
                    if any(pattern in post.text.lower() for pattern in self.filter_patterns['deleted']):
                        continue
                
                # Check for moderator messages
                if any(pattern in combined_text for pattern in self.filter_patterns['moderator']):
                    continue
                
                # Check for welcome messages
                if any(pattern in combined_text for pattern in self.filter_patterns['welcome']):
                    continue
                
                # Check for spam patterns
                if any(pattern in combined_text for pattern in self.filter_patterns['spam']):
                    continue
                
                filtered.append(post)
                
            except Exception as e:
                logger.warning(f"Error filtering post {post.id}: {e}")
                continue
        
        return filtered
    
    async def _normalize_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Normalize post data format and clean text."""
        normalized = []
        
        for post in posts:
            try:
                # Clean and normalize text
                cleaned_text = self._clean_text(post.text)
                
                # Truncate text if too long
                if len(cleaned_text) > self.config.max_text_length:
                    cleaned_text = cleaned_text[:self.config.max_text_length] + "..."
                
                # Create normalized post
                normalized_post = RedditPost(
                    id=post.id,
                    text=cleaned_text,
                    data_type=post.data_type,
                    title=post.title,
                    community=post.community,
                    up_votes=post.up_votes,
                    down_votes=post.down_votes,
                    post_id=post.post_id,
                    parent_id=post.parent_id,
                    author=post.author,
                    created_at=post.created_at,
                    url=post.url,
                    brand_name=post.brand_name,
                    company_url=post.company_url,
                    sentiment=post.sentiment,
                    confidence=post.confidence,
                    themes=post.themes
                )
                
                normalized.append(normalized_post)
                
            except Exception as e:
                logger.warning(f"Error normalizing post {post.id}: {e}")
                continue
        
        return normalized
    
    async def _deduplicate_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Remove duplicate posts based on URL and text similarity."""
        if not self.config.remove_duplicates:
            return posts
        
        seen = set()
        deduplicated = []
        
        for post in posts:
            try:
                # Create a key for deduplication
                # Use URL if available, otherwise use first 160 chars of text
                key = post.url or post.text[:160]
                
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(post)
                
            except Exception as e:
                logger.warning(f"Error deduplicating post {post.id}: {e}")
                continue
        
        return deduplicated
    
    async def _apply_limits(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Apply final limits on number of posts and text length."""
        # Sort by upvotes (descending) to keep most relevant posts
        sorted_posts = sorted(posts, key=lambda p: p.up_votes or 0, reverse=True)
        
        # Apply post count limit
        limited_posts = sorted_posts[:self.config.max_posts]
        
        return limited_posts
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common Reddit artifacts
        text = re.sub(r'\[deleted\]', '', text)
        text = re.sub(r'\[removed\]', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{3,}', '!!!', text)
        text = re.sub(r'[?]{3,}', '???', text)
        
        # Remove URLs (but keep the text)
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove Reddit-specific formatting
        text = re.sub(r'/u/\w+', '', text)
        text = re.sub(r'/r/\w+', '', text)
        
        return text.strip()
    
    async def get_processing_stats(self, original_count: int, final_count: int) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "original_posts": original_count,
            "final_posts": final_count,
            "filtered_posts": original_count - final_count,
            "retention_rate": (final_count / original_count * 100) if original_count > 0 else 0,
            "processing_config": self.config.dict()
        }
    
    async def close(self) -> None:
        """Close the data processor."""
        logger.info("Closing data processor")
        self._initialized = False
