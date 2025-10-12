#!/usr/bin/env python3
"""
Debug script to see what data we get from Reddit scraper
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


async def debug_scraper_data():
    """Debug what data we get from Reddit scraper."""
    print("🐛 Debug: Reddit Scraper Data")
    print("=" * 50)
    
    # Get credentials
    apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not apify_token:
        print("❌ APIFY_API_KEY or APIFY_TOKEN not found")
        return
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found")
        return
    
    # Initialize clients
    supabase = create_client(supabase_url, supabase_key)
    apify_base_url = "https://api.apify.com/v2"
    
    print(f"🔑 Apify Token: {apify_token[:10]}...")
    print(f"🔗 Supabase URL: {supabase_url}")
    
    # Get one URL from database
    print("\n📖 Getting one URL from brand_google_reddit table...")
    try:
        response = supabase.table('brand_google_reddit').select('*').limit(1).execute()
        
        if not response.data:
            print("❌ No URLs found in brand_google_reddit table")
            return
        
        url_data = response.data[0]
        print(f"✅ Found URL: {url_data['title']}")
        print(f"   URL: {url_data['url']}")
        print(f"   Brand: {url_data['brand_name']}")
        
    except Exception as e:
        print(f"❌ Error loading URL from database: {e}")
        return
    
    # Scrape the Reddit URL
    print(f"\n📡 Scraping Reddit URL...")
    print(f"   URL: {url_data['url']}")
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "startUrls": [{"url": url_data['url']}],
                "maxPosts": 1,
                "maxComments": 10,  # Small number for debugging
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,
                "proxy": {"useApifyProxy": True}
            }
            
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                reddit_data = response.json()
                print(f"✅ Successfully scraped {len(reddit_data)} items")
                
                # Save raw data to file for inspection
                debug_file = f"debug_reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(reddit_data, f, indent=2, ensure_ascii=False)
                print(f"💾 Raw data saved to: {debug_file}")
                
                # Show structure of first few items
                print(f"\n🔍 Data Structure Analysis:")
                for i, item in enumerate(reddit_data[:3], 1):
                    print(f"\n--- Item {i} ---")
                    print(f"   Data Type: {item.get('dataType', 'MISSING')}")
                    print(f"   ID: {item.get('id', 'MISSING')}")
                    print(f"   URL: {item.get('url', 'MISSING')}")
                    print(f"   Community: {item.get('communityName', 'MISSING')}")
                    print(f"   Upvotes: {item.get('upVotes', 'MISSING')}")
                    print(f"   Created: {item.get('createdAt', 'MISSING')}")
                    print(f"   All Keys: {list(item.keys())}")
                    
                    if item.get('dataType') == 'post':
                        print(f"   Title: {item.get('title', 'MISSING')}")
                        print(f"   Comments Count: {item.get('commentsCount', 'MISSING')}")
                    elif item.get('dataType') == 'comment':
                        print(f"   Post ID: {item.get('postId', 'MISSING')}")
                        print(f"   Parent ID: {item.get('parentId', 'MISSING')}")
                        print(f"   Body (first 100 chars): {item.get('body', 'MISSING')[:100]}...")
                
                # Now test the processing
                print(f"\n🔄 Testing Data Processing:")
                processed_data = []
                brand_name = url_data['brand_name']
                
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
                        print(f"   ✅ Processed POST: {item.get('id', 'NO_ID')}")
                        
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
                            'number_of_replies': 0,
                            'data_type': 'comment',
                            'brand_name': brand_name
                        }
                        processed_data.append(processed_item)
                        print(f"   ✅ Processed COMMENT: {item.get('id', 'NO_ID')}")
                
                print(f"\n📊 Processing Summary:")
                posts = [item for item in processed_data if item['data_type'] == 'post']
                comments = [item for item in processed_data if item['data_type'] == 'comment']
                print(f"   Total processed: {len(processed_data)}")
                print(f"   Posts: {len(posts)}")
                print(f"   Comments: {len(comments)}")
                
                # Show what we would insert
                print(f"\n💾 Data to be inserted:")
                for i, item in enumerate(processed_data[:2], 1):
                    print(f"   {i}. {item['data_type']} - {item['brand_name']}")
                    print(f"      URL: {item['url']}")
                    print(f"      Community: {item['community_name']}")
                    print(f"      Upvotes: {item['up_votes']}")
                    print()
                
                if len(processed_data) > 2:
                    print(f"   ... and {len(processed_data) - 2} more items")
                
            else:
                print(f"❌ Error scraping Reddit: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception during scraping: {e}")


if __name__ == "__main__":
    asyncio.run(debug_scraper_data())
