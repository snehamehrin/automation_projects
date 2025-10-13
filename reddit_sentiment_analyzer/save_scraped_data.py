#!/usr/bin/env python3
"""
Save scraped Reddit data to a temporary file for processing
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

import httpx
from supabase import create_client, Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('save_scraped_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataSaver:
    """Save scraped Reddit data to temporary files."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.apify_token:
            logger.error("APIFY_API_KEY or APIFY_TOKEN not found")
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found")
        if not self.supabase_url or not self.supabase_key:
            logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.apify_base_url = "https://api.apify.com/v2"
        logger.info("✅ DataSaver initialized successfully")
    
    async def get_urls_from_db(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get unprocessed URLs from brand_google_reddit table."""
        logger.info(f"🔍 Getting {limit} URLs from database...")
        try:
            response = self.supabase.table('brand_google_reddit').select('*').eq('processed', False).limit(limit).execute()
            
            if response.data:
                logger.info(f"✅ Loaded {len(response.data)} URLs from database")
                return response.data
            else:
                logger.warning("❌ No unprocessed URLs found in database")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error loading URLs from database: {e}")
            return []
    
    async def scrape_and_save_data(self, limit: int = 5):
        """Scrape Reddit data and save to temporary files."""
        logger.info("🚀 Starting Reddit Data Scraping and Saving")
        logger.info("=" * 60)
        
        # Get URLs from database
        urls = await self.get_urls_from_db(limit)
        
        if not urls:
            logger.warning("❌ No URLs found in database")
            return
        
        logger.info(f"📊 Found {len(urls)} URLs to scrape")
        
        # Create results directory
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        all_scraped_data = []
        
        async with httpx.AsyncClient() as client:
            for i, url_data in enumerate(urls, 1):
                logger.info(f"\n📡 Scraping {i}/{len(urls)}: {url_data['title'][:50]}...")
                logger.info(f"   URL: {url_data['url']}")
                
                try:
                    # Scrape the data
                    reddit_data = await self._scrape_reddit_url(client, url_data['url'])
                    
                    if reddit_data:
                        logger.info(f"   ✅ Scraped {len(reddit_data)} items")
                        
                        # Save individual file
                        filename = results_dir / f"reddit_data_{url_data['brand_name'].lower().replace(' ', '_')}_{i}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump({
                                'source_url_data': url_data,
                                'reddit_data': reddit_data,
                                'scraped_at': datetime.now().isoformat(),
                                'summary': {
                                    'total_items': len(reddit_data),
                                    'posts': len([item for item in reddit_data if item.get('dataType') == 'post']),
                                    'comments': len([item for item in reddit_data if item.get('dataType') == 'comment'])
                                }
                            }, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"   💾 Saved to: {filename}")
                        
                        # Add to combined data
                        all_scraped_data.extend(reddit_data)
                        
                    else:
                        logger.warning(f"   ❌ No data scraped")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error: {e}")
                    continue
        
        # Save combined data
        if all_scraped_data:
            combined_filename = results_dir / f"all_reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(combined_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_items': len(all_scraped_data),
                    'posts': len([item for item in all_scraped_data if item.get('dataType') == 'post']),
                    'comments': len([item for item in all_scraped_data if item.get('dataType') == 'comment']),
                    'data': all_scraped_data
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n💾 Combined data saved to: {combined_filename}")
            logger.info(f"📊 Total items scraped: {len(all_scraped_data)}")
            
            # Show sample data
            if all_scraped_data:
                sample = all_scraped_data[0]
                logger.info(f"\n📄 Sample data structure:")
                logger.info(f"   Keys: {list(sample.keys())}")
                logger.info(f"   DataType: {sample.get('dataType')}")
                logger.info(f"   Body preview: {sample.get('body', '')[:100]}...")
        else:
            logger.warning("❌ No data was scraped")
    
    async def _scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL using Apify."""
        logger.info(f"🔍 Scraping Reddit URL: {url}")
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,
                "proxy": {"useApifyProxy": True}
            }
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            logger.info(f"Apify response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Raw response data type: {type(data)}")
                
                # Handle different response structures
                if isinstance(data, dict):
                    if 'data' in data:
                        actual_data = data['data']
                        logger.info(f"✅ Found data in 'data' key, length: {len(actual_data)}")
                        return actual_data
                    elif 'items' in data:
                        actual_data = data['items']
                        logger.info(f"✅ Found data in 'items' key, length: {len(actual_data)}")
                        return actual_data
                    else:
                        logger.warning(f"Unexpected data structure: {list(data.keys())}")
                        return []
                elif isinstance(data, list):
                    logger.info(f"✅ Successfully scraped {len(data)} items from {url}")
                    return data
                else:
                    logger.warning(f"Unexpected data type: {type(data)}")
                    return []
            else:
                logger.error(f"❌ Apify error: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return []


async def main():
    """Main function."""
    logger.info("🚀 Reddit Data Scraper and Saver")
    logger.info("=" * 60)
    
    try:
        saver = DataSaver()
        
        # Get number of URLs to scrape
        limit = input("Enter number of URLs to scrape (default 3): ").strip()
        if not limit:
            limit = 3
        else:
            limit = int(limit)
        
        logger.info(f"🎯 Will scrape {limit} URLs")
        
        # Scrape and save data
        await saver.scrape_and_save_data(limit)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
