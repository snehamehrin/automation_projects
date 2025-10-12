"""
Apify service for web scraping and search functionality.

This service handles interactions with Apify's Google Search Scraper and
Reddit Scraper to gather data for sentiment analysis.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from ..utils.logging import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)


class ApifyService:
    """
    Service for interacting with Apify's scraping actors.
    
    Handles Google Search scraping and Reddit content scraping using
    Apify's cloud-based scraping infrastructure.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Apify service."""
        self.settings = get_settings()
        self.api_key = api_key or self.settings.apify_api_key
        self.base_url = "https://api.apify.com/v2"
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service and create HTTP client."""
        if self._initialized:
            return
        
        logger.info("Initializing Apify service")
        
        if not self.api_key:
            raise ValueError("Apify API key is required")
        
        # Create HTTP client with proper headers
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "RedditSentimentAnalyzer/1.0.0"
            },
            timeout=httpx.Timeout(300.0)  # 5 minute timeout for long-running scrapes
        )
        
        self._initialized = True
        logger.info("Apify service initialized successfully")
    
    async def google_search(
        self, 
        query: str, 
        max_results: int = 50,
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Perform Google search using Apify's Google Search Scraper.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            country: Country code for search results
            language: Language code for search results
            
        Returns:
            Dictionary containing search results
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Performing Google search: {query}")
        
        # Prepare request payload
        payload = {
            "queries": [query],
            "maxResultsPerQuery": max_results,
            "countryCode": country,
            "languageCode": language,
            "maxConcurrency": 1,
            "saveHtml": False,
            "saveHtmlToKeyValueStore": False,
            "includeUnfilteredResults": False,
            "customMapFunction": None,
            "maxRetries": 3,
            "waitFor": 0,
            "maxRequestRetries": 3
        }
        
        try:
            # Run the Google Search Scraper
            response = await self.client.post(
                f"{self.base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                json=payload
            )
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Google search completed: {len(results)} results")
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Google search: {e}")
            raise
        except Exception as e:
            logger.error(f"Error performing Google search: {e}")
            raise
    
    async def scrape_reddit(
        self, 
        url: str, 
        max_posts: int = 1,
        max_comments: int = 20,
        max_communities: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Scrape Reddit content using Apify's Reddit Scraper.
        
        Args:
            url: Reddit URL to scrape
            max_posts: Maximum number of posts to scrape
            max_comments: Maximum number of comments per post
            max_communities: Maximum number of communities to scrape
            
        Returns:
            List of Reddit posts and comments
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Scraping Reddit content from: {url}")
        
        # Prepare request payload
        payload = {
            "startUrls": [{"url": url}],
            "maxPosts": max_posts,
            "maxComments": max_comments,
            "maxCommunitiesCount": max_communities,
            "scrollTimeout": 40,
            "proxy": {
                "useApifyProxy": True
            },
            "extendOutputFunction": None,
            "customMapFunction": None,
            "maxRequestRetries": 3,
            "waitFor": 0
        }
        
        try:
            # Run the Reddit Scraper
            response = await self.client.post(
                f"{self.base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                json=payload
            )
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Reddit scraping completed: {len(results)} items")
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Reddit scraping: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scraping Reddit content: {e}")
            raise
    
    async def scrape_reddit_batch(
        self, 
        urls: List[str], 
        max_posts_per_url: int = 1,
        max_comments_per_post: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple Reddit URLs in batch.
        
        Args:
            urls: List of Reddit URLs to scrape
            max_posts_per_url: Maximum posts per URL
            max_comments_per_post: Maximum comments per post
            
        Returns:
            List of all scraped Reddit content
        """
        if not urls:
            return []
        
        logger.info(f"Scraping {len(urls)} Reddit URLs in batch")
        
        # Create tasks for concurrent scraping
        tasks = []
        for url in urls:
            task = self.scrape_reddit(
                url=url,
                max_posts=max_posts_per_url,
                max_comments=max_comments_per_post
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results and filter out exceptions
        all_content = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to scrape URL {urls[i]}: {result}")
            else:
                all_content.extend(result)
        
        logger.info(f"Batch scraping completed: {len(all_content)} total items")
        return all_content
    
    async def get_actor_info(self, actor_id: str) -> Dict[str, Any]:
        """
        Get information about an Apify actor.
        
        Args:
            actor_id: Apify actor ID
            
        Returns:
            Actor information dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.client.get(f"{self.base_url}/acts/{actor_id}")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting actor info: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting actor info: {e}")
            raise
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get Apify usage statistics for the account.
        
        Returns:
            Usage statistics dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.client.get(f"{self.base_url}/users/me/usage")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting usage stats: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test connection to Apify API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Try to get user info
            response = await self.client.get(f"{self.base_url}/users/me")
            response.raise_for_status()
            
            logger.info("Successfully connected to Apify API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Apify API: {e}")
            return False
    
    async def close(self) -> None:
        """Close the service and clean up resources."""
        logger.info("Closing Apify service")
        
        if self.client:
            await self.client.aclose()
            self.client = None
        
        self._initialized = False
