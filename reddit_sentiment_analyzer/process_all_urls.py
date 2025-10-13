#!/usr/bin/env python3
"""
Process all URLs from brand_google_reddit table and scrape Reddit data
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

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
        logging.FileHandler('reddit_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RedditProcessor:
    """Process all URLs from brand_google_reddit table and scrape Reddit data."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.apify_base_url = "https://api.apify.com/v2"
        
        if not self.apify_token:
            logger.error("APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase URL or Key not found in .env")
            raise ValueError("Supabase URL or Key not found in .env. Please configure SUPABASE_URL and SUPABASE_KEY.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info(f"🔑 Apify Token: {self.apify_token[:10]}...")
        logger.info(f"🔗 Supabase URL: {self.supabase_url}")
        logger.info("✅ RedditProcessor initialized successfully")
    
    async def get_all_unprocessed_urls(self) -> list:
        """Get all unprocessed URLs from brand_google_reddit table."""
        logger.info("📖 Fetching all unprocessed URLs from brand_google_reddit table...")
        try:
            # Get all unprocessed URLs
            response = self.supabase.table('brand_google_reddit').select('*').eq('processed', False).execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} unprocessed URLs")
                return response.data
            else:
                logger.warning("❌ No unprocessed URLs found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error loading URLs from database: {e}")
            return []
    
    async def scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> list:
        """Scrape a single Reddit URL using Apify."""
        logger.info(f"🔍 Scraping Reddit URL: {url}")
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,  # Get ALL comments
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,
                "proxy": {"useApifyProxy": True}
            }
            
            logger.debug(f"Apify payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            logger.info(f"Apify response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Successfully scraped {len(data)} items from {url}")
                return data
            else:
                logger.error(f"❌ Error scraping Reddit: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Exception during scraping: {e}")
            return []
    
    def process_reddit_data(self, reddit_data: list, brand_name: str, prospect_id: str = None) -> list:
        """Process Reddit data into the correct format for database."""
        logger.info(f"🔄 Processing {len(reddit_data)} Reddit items for brand: {brand_name}")
        processed_data = []
        
        posts_count = 0
        comments_count = 0
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
                # Extract post body text (title + body)
                title = item.get('title', '')
                body = item.get('body', '')
                full_text = f"{title}. {body}".strip()
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('id', ''),
                    'parent_id': None,
                    'category': 'post',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('commentsCount', 0),
                    'data_type': 'post',
                    'brand_name': brand_name,
                    'body': full_text,  # Add the body text
                    'prospect_id': prospect_id  # Add prospect_id
                }
                processed_data.append(processed_item)
                posts_count += 1
                logger.debug(f"Processed post: {title[:50]}...")
                
            elif item.get('dataType') == 'comment':
                # Extract comment body text
                comment_body = item.get('body', '')
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),
                    'parent_id': item.get('parentId', ''),
                    'category': 'comment',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfreplies', 0),
                    'data_type': 'comment',
                    'brand_name': brand_name,
                    'body': comment_body,  # Add the body text
                    'prospect_id': prospect_id  # Add prospect_id
                }
                processed_data.append(processed_item)
                comments_count += 1
                logger.debug(f"Processed comment: {comment_body[:50]}...")
        
        logger.info(f"✅ Processed {posts_count} posts and {comments_count} comments")
        return processed_data
    
    async def save_reddit_data(self, reddit_data: list) -> bool:
        """Save Reddit data to brand_reddit_posts_comments table."""
        if not reddit_data:
            logger.warning("No data to save")
            return False
            
        logger.info(f"💾 Attempting to save {len(reddit_data)} items to database...")
        try:
            # Log sample data structure
            if reddit_data:
                sample_item = reddit_data[0]
                logger.debug(f"Sample item structure: {list(sample_item.keys())}")
                logger.debug(f"Sample item: {json.dumps(sample_item, indent=2, default=str)}")
            
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                logger.info(f"✅ Successfully saved {len(response.data)} items to database")
                return True
            else:
                logger.error("❌ No data returned from database insert")
                logger.error(f"Response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    async def mark_urls_as_processed(self, url_ids: list) -> bool:
        """Mark URLs as processed in the brand_google_reddit table."""
        logger.info(f"🏷️ Marking {len(url_ids)} URLs as processed...")
        try:
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            
            if response.data:
                logger.info(f"✅ Marked {len(response.data)} URLs as processed")
                return True
            else:
                logger.error("❌ Failed to mark URLs as processed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error marking URLs as processed: {e}")
            return False
    
    async def process_all_urls(self, batch_size: int = 5):
        """Process all unprocessed URLs in batches."""
        logger.info("🚀 Starting Reddit Data Processing for All URLs")
        logger.info("=" * 60)
        
        # Get all unprocessed URLs
        urls = await self.get_all_unprocessed_urls()
        
        if not urls:
            logger.warning("❌ No URLs to process")
            return
        
        logger.info(f"📊 Total URLs to process: {len(urls)}")
        logger.info(f"📦 Processing in batches of {batch_size}")
        
        total_processed = 0
        total_saved = 0
        total_failed = 0
        
        # Process URLs in batches
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(urls) + batch_size - 1) // batch_size
            
            logger.info(f"\n📦 Processing Batch {batch_num}/{total_batches}")
            logger.info(f"   URLs: {i+1}-{min(i+batch_size, len(urls))} of {len(urls)}")
            
            batch_processed = []
            batch_saved = 0
            
            async with httpx.AsyncClient() as client:
                for j, url_data in enumerate(batch, 1):
                    url = url_data['url']
                    brand_name = url_data['brand_name']
                    url_id = url_data['id']
                    prospect_id = url_data.get('prospect_id')  # Get prospect_id if available
                    
                    logger.info(f"\n   🔍 Processing {j}/{len(batch)}: {brand_name}")
                    logger.info(f"      URL: {url}")
                    if prospect_id:
                        logger.info(f"      Prospect ID: {prospect_id}")
                    
                    # Scrape Reddit data
                    reddit_data = await self.scrape_reddit_url(client, url)
                    
                    if reddit_data:
                        # Process the data
                        processed_data = self.process_reddit_data(reddit_data, brand_name, prospect_id)
                        
                        # Save to database
                        if await self.save_reddit_data(processed_data):
                            batch_processed.append(url_id)
                            batch_saved += len(processed_data)
                            
                            posts = [item for item in processed_data if item['data_type'] == 'post']
                            comments = [item for item in processed_data if item['data_type'] == 'comment']
                            logger.info(f"      ✅ Saved: {len(posts)} posts, {len(comments)} comments")
                        else:
                            logger.error(f"      ❌ Failed to save data")
                            total_failed += 1
                    else:
                        logger.warning(f"      ❌ No data scraped")
                        total_failed += 1
                    
                    total_processed += 1
            
            # Mark batch URLs as processed
            if batch_processed:
                await self.mark_urls_as_processed(batch_processed)
            
            logger.info(f"\n   📊 Batch {batch_num} Summary:")
            logger.info(f"      URLs processed: {len(batch)}")
            logger.info(f"      Items saved: {batch_saved}")
            logger.info(f"      URLs marked as processed: {len(batch_processed)}")
        
        # Final summary
        logger.info(f"\n🎉 Processing Complete!")
        logger.info(f"=" * 30)
        logger.info(f"📊 Total URLs processed: {total_processed}")
        logger.info(f"💾 Total items saved: {total_saved}")
        logger.info(f"❌ Total failed: {total_failed}")
        logger.info(f"✅ Success rate: {((total_processed - total_failed) / total_processed * 100):.1f}%")


async def main():
    """Main function to run the Reddit processing."""
    processor = RedditProcessor()
    
    # Ask user for batch size
    try:
        batch_size = int(input("Enter batch size (default 5): ") or "5")
    except ValueError:
        batch_size = 5
    
    # Process all URLs
    await processor.process_all_urls(batch_size)


if __name__ == "__main__":
    asyncio.run(main())
