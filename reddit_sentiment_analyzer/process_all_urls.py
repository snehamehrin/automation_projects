#!/usr/bin/env python3
"""
Process all URLs from brand_google_reddit table and scrape Reddit data
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client
import httpx


class RedditProcessor:
    """Process all URLs from brand_google_reddit table and scrape Reddit data."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.apify_base_url = "https://api.apify.com/v2"
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL or Key not found in .env. Please configure SUPABASE_URL and SUPABASE_KEY.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print(f"🔑 Apify Token: {self.apify_token[:10]}...")
        print(f"🔗 Supabase URL: {self.supabase_url}")
    
    async def get_all_unprocessed_urls(self) -> list:
        """Get all unprocessed URLs from brand_google_reddit table."""
        print("\n📖 Fetching all unprocessed URLs from brand_google_reddit table...")
        try:
            # Get all unprocessed URLs
            response = self.supabase.table('brand_google_reddit').select('*').eq('processed', False).execute()
            
            if response.data:
                print(f"✅ Found {len(response.data)} unprocessed URLs")
                return response.data
            else:
                print("❌ No unprocessed URLs found")
                return []
                
        except Exception as e:
            print(f"❌ Error loading URLs from database: {e}")
            return []
    
    async def scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> list:
        """Scrape a single Reddit URL using Apify."""
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,  # Get ALL comments
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
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"❌ Error scraping Reddit: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception during scraping: {e}")
            return []
    
    def process_reddit_data(self, reddit_data: list, brand_name: str) -> list:
        """Process Reddit data into the correct format for database."""
        processed_data = []
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
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
                    'brand_name': brand_name
                }
                processed_data.append(processed_item)
                
            elif item.get('dataType') == 'comment':
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
                    'brand_name': brand_name
                }
                processed_data.append(processed_item)
        
        return processed_data
    
    async def save_reddit_data(self, reddit_data: list) -> bool:
        """Save Reddit data to brand_reddit_posts_comments table."""
        if not reddit_data:
            return False
            
        try:
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                print(f"✅ Successfully saved {len(response.data)} items to database")
                return True
            else:
                print("❌ No data returned from database insert")
                return False
                
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return False
    
    async def mark_urls_as_processed(self, url_ids: list) -> bool:
        """Mark URLs as processed in the brand_google_reddit table."""
        try:
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            
            if response.data:
                print(f"✅ Marked {len(response.data)} URLs as processed")
                return True
            else:
                print("❌ Failed to mark URLs as processed")
                return False
                
        except Exception as e:
            print(f"❌ Error marking URLs as processed: {e}")
            return False
    
    async def process_all_urls(self, batch_size: int = 5):
        """Process all unprocessed URLs in batches."""
        print("🚀 Starting Reddit Data Processing for All URLs")
        print("=" * 60)
        
        # Get all unprocessed URLs
        urls = await self.get_all_unprocessed_urls()
        
        if not urls:
            print("❌ No URLs to process")
            return
        
        print(f"📊 Total URLs to process: {len(urls)}")
        print(f"📦 Processing in batches of {batch_size}")
        
        total_processed = 0
        total_saved = 0
        total_failed = 0
        
        # Process URLs in batches
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(urls) + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing Batch {batch_num}/{total_batches}")
            print(f"   URLs: {i+1}-{min(i+batch_size, len(urls))} of {len(urls)}")
            
            batch_processed = []
            batch_saved = 0
            
            async with httpx.AsyncClient() as client:
                for j, url_data in enumerate(batch, 1):
                    url = url_data['url']
                    brand_name = url_data['brand_name']
                    url_id = url_data['id']
                    
                    print(f"\n   🔍 Processing {j}/{len(batch)}: {brand_name}")
                    print(f"      URL: {url}")
                    
                    # Scrape Reddit data
                    reddit_data = await self.scrape_reddit_url(client, url)
                    
                    if reddit_data:
                        # Process the data
                        processed_data = self.process_reddit_data(reddit_data, brand_name)
                        
                        # Save to database
                        if await self.save_reddit_data(processed_data):
                            batch_processed.append(url_id)
                            batch_saved += len(processed_data)
                            
                            posts = [item for item in processed_data if item['data_type'] == 'post']
                            comments = [item for item in processed_data if item['data_type'] == 'comment']
                            print(f"      ✅ Saved: {len(posts)} posts, {len(comments)} comments")
                        else:
                            print(f"      ❌ Failed to save data")
                            total_failed += 1
                    else:
                        print(f"      ❌ No data scraped")
                        total_failed += 1
                    
                    total_processed += 1
            
            # Mark batch URLs as processed
            if batch_processed:
                await self.mark_urls_as_processed(batch_processed)
            
            print(f"\n   📊 Batch {batch_num} Summary:")
            print(f"      URLs processed: {len(batch)}")
            print(f"      Items saved: {batch_saved}")
            print(f"      URLs marked as processed: {len(batch_processed)}")
        
        # Final summary
        print(f"\n🎉 Processing Complete!")
        print(f"=" * 30)
        print(f"📊 Total URLs processed: {total_processed}")
        print(f"💾 Total items saved: {total_saved}")
        print(f"❌ Total failed: {total_failed}")
        print(f"✅ Success rate: {((total_processed - total_failed) / total_processed * 100):.1f}%")


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
