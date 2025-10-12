#!/usr/bin/env python3
"""
Test scraping a single Reddit URL to see the data format
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

import httpx
from supabase import create_client, Client


async def test_single_reddit_scrape():
    """Test scraping a single Reddit URL."""
    print("🔍 Testing Single Reddit URL Scraping")
    print("=" * 60)
    
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
    
    # Initialize Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    # Get one unprocessed URL from database
    print("📖 Getting one unprocessed URL from brand_google_reddit table...")
    try:
        response = supabase.table('brand_google_reddit').select('*').eq('processed', False).limit(1).execute()
        
        if not response.data:
            print("❌ No unprocessed URLs found in brand_google_reddit table")
            print("   All URLs may have been processed already, or run the Google search script first")
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
                "maxComments": 1000,  # Get ALL comments
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,  # Increased timeout for more comments
                "proxy": {"useApifyProxy": True}
            }
            
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=120.0  # Increased timeout for more comments
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                reddit_data = response.json()
                print(f"✅ Success! Found {len(reddit_data)} items")
                
                # Analyze the data structure
                print(f"\n📊 Data Structure Analysis:")
                print("=" * 40)
                
                posts = [item for item in reddit_data if item.get('dataType') == 'post']
                comments = [item for item in reddit_data if item.get('dataType') == 'comment']
                
                print(f"   Posts: {len(posts)}")
                print(f"   Comments: {len(comments)}")
                
                # Show post structure
                if posts:
                    print(f"\n📝 POST Structure:")
                    post = posts[0]
                    print(f"   Keys: {list(post.keys())}")
                    print(f"   Sample post data:")
                    for key, value in post.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"     {key}: {value[:100]}...")
                        else:
                            print(f"     {key}: {value}")
                
                # Show comment structure
                if comments:
                    print(f"\n💬 COMMENT Structure:")
                    comment = comments[0]
                    print(f"   Keys: {list(comment.keys())}")
                    print(f"   Sample comment data:")
                    for key, value in comment.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"     {key}: {value[:100]}...")
                        else:
                            print(f"     {key}: {value}")
                
                # Save raw data to file for inspection
                results_dir = Path("results")
                results_dir.mkdir(exist_ok=True)
                
                filename = results_dir / f"reddit_scrape_test_{url_data['brand_name'].lower().replace(' ', '_')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'source_url_data': url_data,
                        'reddit_data': reddit_data,
                        'summary': {
                            'total_items': len(reddit_data),
                            'posts': len(posts),
                            'comments': len(comments),
                            'scraped_at': datetime.now().isoformat()
                        }
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"\n💾 Raw data saved to: {filename}")
                
                # Show sample content
                print(f"\n📄 Sample Content:")
                if posts:
                    post = posts[0]
                    print(f"   POST TITLE: {post.get('title', 'No title')}")
                    print(f"   POST BODY: {post.get('body', 'No body')[:200]}...")
                    print(f"   AUTHOR: {post.get('author', 'Unknown')}")
                    print(f"   COMMUNITY: {post.get('communityName', 'Unknown')}")
                    print(f"   UPVOTES: {post.get('upVotes', 0)}")
                
                if comments:
                    comment = comments[0]
                    print(f"   COMMENT BODY: {comment.get('body', 'No body')[:200]}...")
                    print(f"   COMMENT AUTHOR: {comment.get('author', 'Unknown')}")
                    print(f"   COMMENT UPVOTES: {comment.get('upVotes', 0)}")
                    print(f"   POST ID: {comment.get('postId', 'Unknown')}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print(f"\n🎉 Test completed!")
    print(f"   Check the saved JSON file to see the full data structure")
    print(f"   Use this to design your Supabase table schema")


if __name__ == "__main__":
    asyncio.run(test_single_reddit_scrape())
