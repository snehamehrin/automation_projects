#!/usr/bin/env python3
"""
Scrape Reddit posts and comments with simplified schema
"""

import asyncio
import os
import sys
import json
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


class SimpleRedditScraper:
    """Scrape Reddit posts and comments with simplified schema."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.apify_base_url = "https://api.apify.com/v2"
    
    async def scrape_posts_from_db(self, brand_name: str = None, limit: int = 5):
        """Scrape Reddit posts from URLs in the database."""
        print(f"🔍 Loading Reddit URLs from database...")
        print("=" * 60)
        
        # Get URLs from database
        urls = await self._get_urls_from_db(brand_name, limit)
        
        if not urls:
            print("❌ No URLs found in database")
            return
        
        print(f"📊 Found {len(urls)} URLs to scrape")
        
        # Scrape each URL
        all_reddit_data = []
        
        async with httpx.AsyncClient() as client:
            for i, url_data in enumerate(urls, 1):
                print(f"\n📡 Scraping {i}/{len(urls)}: {url_data['title'][:50]}...")
                print(f"   URL: {url_data['url']}")
                
                try:
                    reddit_data = await self._scrape_reddit_url(client, url_data['url'])
                    
                    if reddit_data:
                        # Process and add metadata
                        processed_data = self._process_reddit_data(reddit_data, url_data['brand_name'])
                        all_reddit_data.extend(processed_data)
                        print(f"   ✅ Found {len(processed_data)} items")
                    else:
                        print(f"   ❌ No data found")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
        
        print(f"\n📊 Total Reddit data collected: {len(all_reddit_data)} items")
        
        if all_reddit_data:
            # Save to database
            await self._save_reddit_data(all_reddit_data)
            
            # Mark URLs as processed
            await self._mark_urls_as_processed(urls)
        else:
            print("❌ No Reddit data collected")
    
    async def _get_urls_from_db(self, brand_name: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get unprocessed URLs from brand_google_reddit table."""
        try:
            query = self.supabase.table('brand_google_reddit').select('*')
            
            if brand_name:
                query = query.eq('brand_name', brand_name)
            
            # Only get unprocessed URLs
            query = query.eq('processed', False)
            query = query.limit(limit)
            
            response = query.execute()
            
            if response.data:
                print(f"✅ Loaded {len(response.data)} unprocessed URLs from database")
                return response.data
            else:
                print("❌ No unprocessed URLs found in database")
                return []
                
        except Exception as e:
            print(f"❌ Error loading URLs from database: {e}")
            return []
    
    async def _scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL using Apify."""
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,  # Get up to 1000 comments per post
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,  # Increased timeout for more comments
                "proxy": {"useApifyProxy": True}
            }
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=120.0  # Increased timeout for more comments
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Apify error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Scraping error: {e}")
            return []
    
    def _process_reddit_data(self, reddit_data: List[Dict[str, Any]], brand_name: str) -> List[Dict[str, Any]]:
        """Process Reddit data to match our simplified schema."""
        processed_data = []
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
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
                    'brand_name': brand_name
                }
                processed_data.append(processed_item)
                
            elif item.get('dataType') == 'comment':
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
                    'brand_name': brand_name
                }
                processed_data.append(processed_item)
        
        return processed_data
    
    async def _mark_urls_as_processed(self, urls: List[Dict[str, Any]]):
        """Mark URLs as processed in the brand_google_reddit table."""
        try:
            url_ids = [url['id'] for url in urls]
            
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            
            if response.data:
                print(f"✅ Marked {len(response.data)} URLs as processed")
            else:
                print("❌ Failed to mark URLs as processed")
                
        except Exception as e:
            print(f"❌ Error marking URLs as processed: {e}")
    
    async def _save_reddit_data(self, reddit_data: List[Dict[str, Any]]):
        """Save Reddit data to database."""
        print(f"\n💾 Saving {len(reddit_data)} Reddit items to database...")
        
        try:
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                print(f"✅ Successfully saved {len(response.data)} Reddit items to database")
                
                # Show summary
                posts_count = len([item for item in reddit_data if item['data_type'] == 'post'])
                comments_count = len([item for item in reddit_data if item['data_type'] == 'comment'])
                
                print(f"\n📋 Summary:")
                print(f"   Posts saved: {posts_count}")
                print(f"   Comments saved: {comments_count}")
                print(f"   Total items: {len(response.data)}")
                print(f"   Table: brand_reddit_posts_comments")
                
                # Show sample data
                print(f"\n📄 Sample data:")
                for i, item in enumerate(response.data[:3], 1):
                    data_type = item.get('data_type', 'unknown')
                    community = item.get('community_name', 'Unknown')
                    upvotes = item.get('up_votes', 0)
                    print(f"   {i}. [{data_type.upper()}] r/{community}")
                    print(f"      Upvotes: {upvotes}")
                    print(f"      Post ID: {item.get('post_id', 'N/A')}")
                    if item.get('parent_id'):
                        print(f"      Parent ID: {item.get('parent_id')}")
                    print()
                
            else:
                print("❌ No data returned from database insert")
                
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            print("   Make sure the 'brand_reddit_posts_comments' table exists with the correct schema")


async def main():
    """Main function."""
    print("🚀 Simple Reddit Posts & Comments Scraper")
    print("=" * 60)
    
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
