"""
Module 2: Google Search for Reddit URLs
Uses Apify to search Google for Reddit discussions
"""

import httpx
from typing import List, Dict, Any
from config.settings import get_settings
from database.db import Database
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class GoogleSearcher:
    def __init__(self):
        self.db = Database()
        self.apify_token = settings.APIFY_API_KEY
        self.apify_actor = "apify~google-search-scraper"
    
    async def search_reddit_urls(self, brand_name: str, category: str = "") -> List[str]:
        """Search Google for Reddit URLs about the brand"""
        # Construct search query - use reddit:brandname format as requested
        search_query = f"reddit:{brand_name}"
        
        logger.info(f"Searching: {search_query}")
        
        # Call Apify actor
        url = f"https://api.apify.com/v2/acts/{self.apify_actor}/run-sync-get-dataset-items"
        params = {"token": self.apify_token}
        headers = {"Content-Type": "application/json"}
        payload = {"queries": search_query, "maxPagesPerQuery": 1}
        
        async with httpx.AsyncClient(timeout=310.0) as client:
            response = await client.post(url, json=payload, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
        
        # Extract Reddit URLs
        reddit_urls = []
        for result in results:
            organic_results = result.get('organicResults', [])
            for item in organic_results:
                url = item.get('url', '')
                if 'reddit.com/r/' in url and url not in reddit_urls:
                    reddit_urls.append(url)
        
        # Limit to MAX_REDDIT_URLS
        reddit_urls = reddit_urls[:settings.MAX_REDDIT_URLS]
        
        logger.info(f"Found {len(reddit_urls)} Reddit URLs")
        return reddit_urls
    
    async def update_prospect_urls(self, prospect_id: str, urls: List[str]) -> None:
        """Store Reddit URLs in database"""
        url_data = [
            {
                'prospect_id': prospect_id,
                'url': url,
                'status': 'pending'
            }
            for url in urls
        ]
        await self.db.insert_reddit_urls(url_data)
        logger.info(f"Stored {len(urls)} URLs for prospect {prospect_id}")
