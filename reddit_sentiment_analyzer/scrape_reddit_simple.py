#!/usr/bin/env python3
"""
Scrape Reddit posts and comments with simplified schema
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
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_reddit_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleRedditScraper:
    """Scrape Reddit posts and comments with simplified schema."""
    
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
        logger.info("✅ SimpleRedditScraper initialized successfully")
    
    async def scrape_posts_from_db(self, brand_name: str = None, limit: int = 5):
        """Scrape Reddit posts from URLs in the database."""
        logger.info(f"🔍 Loading Reddit URLs from database...")
        logger.info("=" * 60)
        
        # Get URLs from database
        urls = await self._get_urls_from_db(brand_name, limit)
        
        if not urls:
            logger.warning("❌ No URLs found in database")
            return
        
        logger.info(f"📊 Found {len(urls)} URLs to scrape")
        
        # Scrape each URL
        all_reddit_data = []
        
        async with httpx.AsyncClient() as client:
            for i, url_data in enumerate(urls, 1):
                logger.info(f"\n📡 Scraping {i}/{len(urls)}: {url_data['title'][:50]}...")
                logger.info(f"   URL: {url_data['url']}")
                
                try:
                    reddit_data = await self._scrape_reddit_url(client, url_data['url'])
                    
                    logger.debug(f"Raw reddit_data type: {type(reddit_data)}")
                    logger.debug(f"Raw reddit_data length: {len(reddit_data) if reddit_data else 0}")
                    
                    if reddit_data:
                        logger.debug(f"About to process {len(reddit_data)} items")
                        # Process and add metadata
                        processed_data = self._process_reddit_data(reddit_data, url_data['brand_name'])
                        logger.debug(f"Processed data length: {len(processed_data)}")
                        all_reddit_data.extend(processed_data)
                        logger.info(f"   ✅ Found {len(processed_data)} items")
                    else:
                        logger.warning(f"   ❌ No data found")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error: {e}")
                    continue
        
        logger.info(f"\n📊 Total Reddit data collected: {len(all_reddit_data)} items")
        
        if all_reddit_data:
            # Save to database
            await self._save_reddit_data(all_reddit_data)
            
            # Mark URLs as processed
            await self._mark_urls_as_processed(urls)
        else:
            logger.warning("❌ No Reddit data collected")
    
    async def _get_urls_from_db(self, brand_name: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get unprocessed URLs from brand_google_reddit table."""
        logger.info(f"🔍 Getting URLs from database (brand: {brand_name}, limit: {limit})")
        try:
            query = self.supabase.table('brand_google_reddit').select('*')
            
            if brand_name:
                query = query.eq('brand_name', brand_name)
            
            # Only get unprocessed URLs
            query = query.eq('processed', False)
            query = query.limit(limit)
            
            response = query.execute()
            
            if response.data:
                logger.info(f"✅ Loaded {len(response.data)} unprocessed URLs from database")
                return response.data
            else:
                logger.warning("❌ No unprocessed URLs found in database")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error loading URLs from database: {e}")
            return []
    
    async def _scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL using Apify."""
        logger.info(f"🔍 Scraping Reddit URL: {url}")
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,  # Get up to 1000 comments per post
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,  # Increased timeout for more comments
                "proxy": {"useApifyProxy": True}
            }
            
            logger.debug(f"Apify payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=120.0  # Increased timeout for more comments
            )
            
            logger.info(f"Apify response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Successfully scraped {len(data)} items from {url}")
                return data
            else:
                logger.error(f"❌ Apify error: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return []
    
    def _process_reddit_data(self, reddit_data: List[Dict[str, Any]], brand_name: str) -> List[Dict[str, Any]]:
        """Process Reddit data to match our simplified schema."""
        logger.info(f"🔄 Processing {len(reddit_data)} Reddit items for brand: {brand_name}")
        processed_data = []
        
        posts_count = 0
        comments_count = 0
        
        # Debug: Log the first item to see the structure
        if reddit_data:
            logger.debug(f"First item structure: {list(reddit_data[0].keys())}")
            logger.debug(f"First item dataType: {reddit_data[0].get('dataType')}")
        
        for item in reddit_data:
            data_type = item.get('dataType')
            logger.debug(f"Processing item with dataType: {data_type}")
            
            if data_type == 'post':
                # Extract post body text (title + body)
                title = item.get('title', '')
                body = item.get('body', '')
                full_text = f"{title}. {body}".strip()
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('id', ''),  # For posts, this is the post ID
                    'parent_id': None,  # Posts don't have parent IDs
                    'category': None,  # We'll need to determine this
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'post',
                    'brand_name': brand_name,
                    'body': full_text  # Add the body text
                }
                processed_data.append(processed_item)
                posts_count += 1
                logger.debug(f"Processed post: {title[:50]}...")
                
            elif data_type == 'comment':
                # Extract comment body text
                comment_body = item.get('body', '')
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),  # Links to parent post
                    'parent_id': item.get('parentId', ''),  # Links to parent comment
                    'category': None,  # We'll need to determine this
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'comment',
                    'brand_name': brand_name,
                    'body': comment_body  # Add the body text
                }
                processed_data.append(processed_item)
                comments_count += 1
                logger.debug(f"Processed comment: {comment_body[:50]}...")
            else:
                logger.warning(f"Unknown dataType: {data_type} for item: {item.get('id', 'unknown')}")
        
        logger.info(f"✅ Processed {posts_count} posts and {comments_count} comments")
        return processed_data
    
    async def _mark_urls_as_processed(self, urls: List[Dict[str, Any]]):
        """Mark URLs as processed in the brand_google_reddit table."""
        logger.info(f"🏷️ Marking {len(urls)} URLs as processed...")
        try:
            url_ids = [url['id'] for url in urls]
            
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            
            if response.data:
                logger.info(f"✅ Marked {len(response.data)} URLs as processed")
            else:
                logger.error("❌ Failed to mark URLs as processed")
                
        except Exception as e:
            logger.error(f"❌ Error marking URLs as processed: {e}")
    
    async def _save_reddit_data(self, reddit_data: List[Dict[str, Any]]):
        """Save Reddit data to database."""
        logger.info(f"💾 Saving {len(reddit_data)} Reddit items to database...")
        
        try:
            # Log sample data structure
            if reddit_data:
                sample_item = reddit_data[0]
                logger.debug(f"Sample item structure: {list(sample_item.keys())}")
                logger.debug(f"Sample item: {json.dumps(sample_item, indent=2, default=str)}")
            
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                logger.info(f"✅ Successfully saved {len(response.data)} Reddit items to database")
                
                # Show summary
                posts_count = len([item for item in reddit_data if item['data_type'] == 'post'])
                comments_count = len([item for item in reddit_data if item['data_type'] == 'comment'])
                
                logger.info(f"📋 Summary:")
                logger.info(f"   Posts saved: {posts_count}")
                logger.info(f"   Comments saved: {comments_count}")
                logger.info(f"   Total items: {len(response.data)}")
                logger.info(f"   Table: brand_reddit_posts_comments")
                
                # Show sample data
                logger.info(f"📄 Sample data:")
                for i, item in enumerate(response.data[:3], 1):
                    data_type = item.get('data_type', 'unknown')
                    community = item.get('community_name', 'Unknown')
                    upvotes = item.get('up_votes', 0)
                    logger.info(f"   {i}. [{data_type.upper()}] r/{community}")
                    logger.info(f"      Upvotes: {upvotes}")
                    logger.info(f"      Post ID: {item.get('post_id', 'N/A')}")
                    if item.get('parent_id'):
                        logger.info(f"      Parent ID: {item.get('parent_id')}")
                    logger.info("")
                
            else:
                logger.error("❌ No data returned from database insert")
                logger.error(f"Response: {response}")
                
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("   Make sure the 'brand_reddit_posts_comments' table exists with the correct schema")


async def main():
    """Main function."""
    logger.info("🚀 Simple Reddit Posts & Comments Scraper")
    logger.info("=" * 60)
    
    try:
        # Initialize scraper
        scraper = SimpleRedditScraper()
        
        # Get parameters
        brand_name = input("Enter brand name to scrape (or press Enter for all brands): ").strip()
        if not brand_name:
            brand_name = None
        
        limit = input("Enter number of URLs to scrape (default 5): ").strip()
        if not limit:
            limit = 5
        else:
            limit = int(limit)
        
        print(f"🎯 Brand: {brand_name or 'All brands'}")
        print(f"📊 Limit: {limit} URLs")
        
        # Check if reddit table exists
        try:
            test_response = scraper.supabase.table('brand_reddit_posts_comments').select('id').limit(1).execute()
            print("✅ Table 'brand_reddit_posts_comments' exists")
        except Exception as e:
            print("❌ Table 'brand_reddit_posts_comments' does not exist")
            print("\n📋 Please create the table in your Supabase SQL Editor:")
            print("""
            CREATE TABLE reddit_posts_comments (
                id UUID NOT NULL DEFAULT gen_random_uuid(),
                url TEXT NOT NULL,
                post_id TEXT,
                parent_id TEXT,
                category TEXT,
                community_name TEXT,
                created_at_reddit TEXT,
                scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                up_votes INTEGER DEFAULT 0,
                number_of_replies INTEGER DEFAULT 0,
                data_type TEXT NOT NULL CHECK (data_type IN ('post', 'comment')),
                brand_name TEXT NOT NULL,
                CONSTRAINT reddit_posts_comments_pkey PRIMARY KEY (id)
            );
            
            -- Create indexes
            CREATE INDEX idx_reddit_posts_comments_brand_name ON reddit_posts_comments(brand_name);
            CREATE INDEX idx_reddit_posts_comments_data_type ON reddit_posts_comments(data_type);
            CREATE INDEX idx_reddit_posts_comments_community_name ON reddit_posts_comments(community_name);
            """)
            return
        
        # Check if source table has data
        try:
            test_response = scraper.supabase.table('brand_google_reddit').select('id').limit(1).execute()
            if test_response.data:
                print("✅ Table 'brand_google_reddit' has data")
            else:
                print("❌ Table 'brand_google_reddit' is empty")
                print("   Please run the Google search script first to populate URLs")
                return
        except Exception as e:
            print("❌ Table 'brand_google_reddit' does not exist")
            print("   Please run the Google search script first")
            return
        
        # Start scraping
        await scraper.scrape_posts_from_db(brand_name, limit)
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
