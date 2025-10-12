#!/usr/bin/env python3
"""
Scrape Reddit posts and comments from URLs stored in brand_google_reddit table
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


class RedditPostScraper:
    """Scrape Reddit posts and comments from database URLs."""
    
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
    
    async def scrape_posts_from_db(self, brand_name: str = None, limit: int = 10):
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
                        # Add metadata to each item
                        for item in reddit_data:
                            item['source_url'] = url_data['url']
                            item['source_title'] = url_data['title']
                            item['brand_name'] = url_data['brand_name']
                            item['scraped_at'] = datetime.now().isoformat()
                        
                        all_reddit_data.extend(reddit_data)
                        print(f"   ✅ Found {len(reddit_data)} items (posts + comments)")
                    else:
                        print(f"   ❌ No data found")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
        
        print(f"\n📊 Total Reddit data collected: {len(all_reddit_data)} items")
        
        if all_reddit_data:
            # Process and save to database
            await self._save_reddit_data(all_reddit_data)
        else:
            print("❌ No Reddit data collected")
    
    async def _get_urls_from_db(self, brand_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get URLs from brand_google_reddit table."""
        try:
            query = self.supabase.table('brand_google_reddit').select('*')
            
            if brand_name:
                query = query.eq('brand_name', brand_name)
            
            query = query.limit(limit)
            
            response = query.execute()
            
            if response.data:
                print(f"✅ Loaded {len(response.data)} URLs from database")
                return response.data
            else:
                print("❌ No URLs found in database")
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
                "maxComments": 20,
                "maxCommunitiesCount": 1,
                "scrollTimeout": 40,
                "proxy": {"useApifyProxy": True}
            }
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ Apify error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Scraping error: {e}")
            return []
    
    async def _save_reddit_data(self, reddit_data: List[Dict[str, Any]]):
        """Save Reddit data to database."""
        print(f"\n💾 Processing and saving {len(reddit_data)} Reddit items...")
        
        # Process data for database
        processed_data = []
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
                processed_item = {
                    'reddit_id': item.get('id', ''),
                    'data_type': 'post',
                    'title': item.get('title', ''),
                    'body': item.get('body', ''),
                    'author': item.get('author', ''),
                    'community_name': item.get('communityName', ''),
                    'up_votes': item.get('upVotes', 0),
                    'down_votes': item.get('downVotes', 0),
                    'created_at_reddit': item.get('createdAt', ''),
                    'url': item.get('url', ''),
                    'source_url': item.get('source_url', ''),
                    'source_title': item.get('source_title', ''),
                    'brand_name': item.get('brand_name', ''),
                    'scraped_at': item.get('scraped_at', ''),
                    'created_at': datetime.now().isoformat()
                }
                processed_data.append(processed_item)
                
            elif item.get('dataType') == 'comment':
                processed_item = {
                    'reddit_id': item.get('id', ''),
                    'data_type': 'comment',
                    'title': '',  # Comments don't have titles
                    'body': item.get('body', ''),
                    'author': item.get('author', ''),
                    'community_name': item.get('communityName', ''),
                    'up_votes': item.get('upVotes', 0),
                    'down_votes': item.get('downVotes', 0),
                    'created_at_reddit': item.get('createdAt', ''),
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),
                    'parent_id': item.get('parentId', ''),
                    'source_url': item.get('source_url', ''),
                    'source_title': item.get('source_title', ''),
                    'brand_name': item.get('brand_name', ''),
                    'scraped_at': item.get('scraped_at', ''),
                    'created_at': datetime.now().isoformat()
                }
                processed_data.append(processed_item)
        
        # Save to database
        try:
            response = self.supabase.table('reddit_posts_comments').insert(processed_data).execute()
            
            if response.data:
                print(f"✅ Successfully saved {len(response.data)} Reddit items to database")
                
                # Show summary
                posts_count = len([item for item in processed_data if item['data_type'] == 'post'])
                comments_count = len([item for item in processed_data if item['data_type'] == 'comment'])
                
                print(f"\n📋 Summary:")
                print(f"   Posts saved: {posts_count}")
                print(f"   Comments saved: {comments_count}")
                print(f"   Total items: {len(response.data)}")
                print(f"   Table: reddit_posts_comments")
                
                # Show sample data
                print(f"\n📄 Sample data:")
                for i, item in enumerate(response.data[:3], 1):
                    data_type = item.get('data_type', 'unknown')
                    title = item.get('title', 'No title')[:50]
                    body = item.get('body', 'No body')[:100]
                    print(f"   {i}. [{data_type.upper()}] {title}...")
                    print(f"      Body: {body}...")
                    print(f"      Author: {item.get('author', 'Unknown')}")
                    print(f"      Upvotes: {item.get('up_votes', 0)}")
                    print()
                
            else:
                print("❌ No data returned from database insert")
                
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            print("   Make sure the 'reddit_posts_comments' table exists")
    
    def get_reddit_table_sql(self):
        """Return SQL to create the reddit_posts_comments table."""
        return """
        CREATE TABLE reddit_posts_comments (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            reddit_id TEXT NOT NULL,
            data_type TEXT NOT NULL CHECK (data_type IN ('post', 'comment')),
            title TEXT,
            body TEXT,
            author TEXT,
            community_name TEXT,
            up_votes INTEGER DEFAULT 0,
            down_votes INTEGER DEFAULT 0,
            created_at_reddit TEXT,
            url TEXT,
            post_id TEXT,  -- For comments, links to parent post
            parent_id TEXT,  -- For comments, links to parent comment
            source_url TEXT,  -- Original URL from brand_google_reddit table
            source_title TEXT,  -- Original title from brand_google_reddit table
            brand_name TEXT NOT NULL,
            scraped_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT reddit_posts_comments_pkey PRIMARY KEY (id)
        );
        
        -- Create indexes
        CREATE INDEX idx_reddit_posts_comments_brand_name ON reddit_posts_comments(brand_name);
        CREATE INDEX idx_reddit_posts_comments_data_type ON reddit_posts_comments(data_type);
        CREATE INDEX idx_reddit_posts_comments_reddit_id ON reddit_posts_comments(reddit_id);
        CREATE INDEX idx_reddit_posts_comments_created_at ON reddit_posts_comments(created_at);
        """


async def main():
    """Main function."""
    print("🚀 Reddit Posts & Comments Scraper")
    print("=" * 60)
    
    try:
        # Initialize scraper
        scraper = RedditPostScraper()
        
        # Get parameters
        brand_name = input("Enter brand name to scrape (or press Enter for all brands): ").strip()
        if not brand_name:
            brand_name = None
        
        limit = input("Enter number of URLs to scrape (default 10): ").strip()
        if not limit:
            limit = 10
        else:
            limit = int(limit)
        
        print(f"🎯 Brand: {brand_name or 'All brands'}")
        print(f"📊 Limit: {limit} URLs")
        
        # Check if reddit table exists
        try:
            test_response = scraper.supabase.table('reddit_posts_comments').select('id').limit(1).execute()
            print("✅ Table 'reddit_posts_comments' exists")
        except Exception as e:
            print("❌ Table 'reddit_posts_comments' does not exist")
            print("\n📋 Please create the table in your Supabase SQL Editor:")
            print(scraper.get_reddit_table_sql())
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
