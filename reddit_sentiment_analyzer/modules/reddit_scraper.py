"""
Module 3: Reddit Scraper
Scrapes posts and comments from Reddit URLs using Apify
"""

import httpx
from typing import List, Dict, Any
from config.settings import get_settings
from database.db import Database
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RedditScraper:
    def __init__(self):
        self.db = Database()
        self.apify_token = settings.APIFY_API_KEY
        self.apify_actor = "trudax~reddit-scraper-lite"
    
    async def scrape_all_urls(
        self, 
        urls: List[str], 
        brand_name: str, 
        prospect_id: str
    ) -> List[Dict[str, Any]]:
        """Scrape all Reddit URLs and store in database"""
        all_data = []
        
        for url in urls:
            logger.info(f"Scraping: {url}")
            try:
                data = await self._scrape_url(url, brand_name, prospect_id)
                all_data.extend(data)
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                continue
        
        # Store in database
        if all_data:
            await self.db.insert_posts_comments(all_data)
            logger.info(f"Stored {len(all_data)} posts/comments for {brand_name}")
        
        return all_data
    
    async def _scrape_url(
        self, 
        url: str, 
        brand_name: str, 
        prospect_id: str
    ) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL"""
        api_url = f"https://api.apify.com/v2/acts/{self.apify_actor}/run-sync-get-dataset-items"
        params = {"token": self.apify_token}
        headers = {"Content-Type": "application/json"}
        payload = {
            "startUrls": [{"url": url}],
            "maxPosts": settings.MAX_POSTS_PER_URL,
            "maxComments": settings.MAX_COMMENTS_PER_POST,
            "maxCommunitiesCount": 1,
            "scrollTimeout": 40,
            "proxy": {"useApifyProxy": True}
        }
        
        async with httpx.AsyncClient(timeout=310.0) as client:
            response = await client.post(api_url, json=payload, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
        
        # Transform to database format
        transformed = []
        for item in results:
            data_type = item.get('dataType', 'post')
            
            record = {
                'url': url,
                'post_id': item.get('id'),
                'parent_id': item.get('postId') if data_type == 'comment' else None,
                'category': item.get('category'),
                'community_name': item.get('communityName'),
                'created_at_reddit': item.get('createdAt'),
                'up_votes': item.get('upVotes', 0),
                'number_of_replies': item.get('numberOfReplies', 0),
                'data_type': data_type,
                'brand_name': brand_name,
                'body': item.get('body') or item.get('title', ''),
                'prospect_id': prospect_id
            }
            transformed.append(record)
        
        return transformed
