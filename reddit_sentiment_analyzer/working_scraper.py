#!/usr/bin/env python3
"""
Working Reddit scraper - simple and direct
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('working_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WorkingScraper:
    """Working Reddit scraper that actually works."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY not found")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE credentials not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ WorkingScraper initialized")
    
    async def scrape_and_save(self, limit: int = 3):
        """Scrape Reddit data and save to database."""
        logger.info("🚀 Starting Reddit scraping")
        
        # Get URLs from database
        try:
            response = self.supabase.table('brand_google_reddit').select('*').eq('processed', False).limit(limit).execute()
            
            if not response.data:
                logger.warning("No URLs found")
                return
            
            urls = response.data
            logger.info(f"Found {len(urls)} URLs to scrape")
            
        except Exception as e:
            logger.error(f"Error getting URLs: {e}")
            return
        
        # Scrape each URL
        all_processed_data = []
        
        async with httpx.AsyncClient() as client:
            for i, url_data in enumerate(urls, 1):
                logger.info(f"\n📡 Scraping {i}/{len(urls)}: {url_data['title'][:50]}...")
                
                try:
                    # Call Apify API
                    payload = {
                        "startUrls": [{"url": url_data['url']}],
                        "maxPosts": 1,
                        "maxComments": 1000,
                        "maxCommunitiesCount": 1,
                        "scrollTimeout": 60,
                        "proxy": {"useApifyProxy": True}
                    }
                    
                    response = await client.post(
                        "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                        headers={"Authorization": f"Bearer {self.apify_token}"},
                        json=payload,
                        timeout=120.0
                    )
                    
                    logger.info(f"Apify response: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Got data type: {type(data)}")
                        
                        # Handle the data
                        if isinstance(data, list):
                            reddit_data = data
                        elif isinstance(data, dict) and 'data' in data:
                            reddit_data = data['data']
                        elif isinstance(data, dict) and 'items' in data:
                            reddit_data = data['items']
                        else:
                            logger.warning(f"Unexpected data structure: {type(data)}")
                            continue
                        
                        logger.info(f"Processing {len(reddit_data)} items")
                        
                        # Process the data
                        processed_data = self.process_data(reddit_data, url_data['brand_name'])
                        all_processed_data.extend(processed_data)
                        
                        logger.info(f"✅ Processed {len(processed_data)} items")
                        
                    else:
                        logger.error(f"Apify error: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error scraping: {e}")
                    continue
        
        # Save all data to database
        if all_processed_data:
            logger.info(f"\n💾 Saving {len(all_processed_data)} items to database...")
            
            try:
                response = self.supabase.table('brand_reddit_posts_comments').insert(all_processed_data).execute()
                
                if response.data:
                    logger.info(f"✅ Successfully saved {len(response.data)} items to database")
                    
                    # Mark URLs as processed
                    url_ids = [url['id'] for url in urls]
                    self.supabase.table('brand_google_reddit').update({'processed': True}).in_('id', url_ids).execute()
                    
                    logger.info("✅ Marked URLs as processed")
                else:
                    logger.error("❌ Failed to save to database")
                    
            except Exception as e:
                logger.error(f"❌ Database error: {e}")
        else:
            logger.warning("No data to save")
    
    def process_data(self, reddit_data: List[Dict], brand_name: str) -> List[Dict]:
        """Process Reddit data for database."""
        processed = []
        
        for item in reddit_data:
            data_type = item.get('dataType')
            
            if data_type == 'post':
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('id', ''),
                    'parent_id': None,
                    'category': 'post',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'post',
                    'brand_name': brand_name,
                    'body': f"{item.get('title', '')}. {item.get('body', '')}".strip()
                }
                processed.append(processed_item)
                
            elif data_type == 'comment':
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),
                    'parent_id': item.get('parentId', ''),
                    'category': 'comment',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'comment',
                    'brand_name': brand_name,
                    'body': item.get('body', '')
                }
                processed.append(processed_item)
        
        return processed


async def main():
    """Main function."""
    try:
        scraper = WorkingScraper()
        await scraper.scrape_and_save(3)
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
