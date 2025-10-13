#!/usr/bin/env python3
"""
Debug script to see exactly what's happening
"""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import httpx
from supabase import create_client, Client


async def debug_scrape():
    """Debug the scraping process step by step."""
    print("🔍 DEBUG: Step by step scraping")
    print("=" * 50)
    
    # Get credentials
    apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"✅ Apify token: {apify_token[:10]}...")
    print(f"✅ Supabase URL: {supabase_url}")
    
    # Get one URL from database
    supabase = create_client(supabase_url, supabase_key)
    try:
        response = supabase.table('brand_google_reddit').select('*').eq('processed', False).limit(1).execute()
        
        if not response.data:
            print("❌ No URLs found")
            return
        
        url_data = response.data[0]
        print(f"✅ Found URL: {url_data['title']}")
        print(f"   URL: {url_data['url']}")
        
    except Exception as e:
        print(f"❌ Error getting URL: {e}")
        return
    
    # Scrape with Apify
    print(f"\n📡 Calling Apify API...")
    
    async with httpx.AsyncClient() as client:
        try:
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
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            print(f"✅ Response Status: {response.status_code}")
            
            if response.status_code == 200:
                # Get the raw response
                raw_data = response.json()
                
                print(f"✅ Got response!")
                print(f"   Type: {type(raw_data)}")
                
                # Check if it's a list
                if isinstance(raw_data, list):
                    print(f"   List length: {len(raw_data)}")
                    if raw_data:
                        print(f"   First item keys: {list(raw_data[0].keys())}")
                        print(f"   First item dataType: {raw_data[0].get('dataType')}")
                        print(f"   First item body: {raw_data[0].get('body', '')[:100]}...")
                    
                    # Save the data
                    results_dir = Path("results")
                    results_dir.mkdir(exist_ok=True)
                    
                    filename = results_dir / f"debug_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({
                            'source_url': url_data['url'],
                            'brand_name': url_data['brand_name'],
                            'scraped_at': datetime.now().isoformat(),
                            'data': raw_data,
                            'total_items': len(raw_data),
                            'posts': len([item for item in raw_data if item.get('dataType') == 'post']),
                            'comments': len([item for item in raw_data if item.get('dataType') == 'comment'])
                        }, f, indent=2, ensure_ascii=False)
                    
                    print(f"\n💾 Data saved to: {filename}")
                    print(f"📊 Total items: {len(raw_data)}")
                    print(f"📊 Posts: {len([item for item in raw_data if item.get('dataType') == 'post'])}")
                    print(f"📊 Comments: {len([item for item in raw_data if item.get('dataType') == 'comment'])}")
                    
                    # Show sample data
                    if raw_data:
                        print(f"\n📄 Sample data:")
                        sample = raw_data[0]
                        print(f"   ID: {sample.get('id')}")
                        print(f"   DataType: {sample.get('dataType')}")
                        print(f"   Body: {sample.get('body', '')[:200]}...")
                        print(f"   Community: {sample.get('communityName')}")
                        print(f"   Upvotes: {sample.get('upVotes')}")
                
                # Check if it's a dict
                elif isinstance(raw_data, dict):
                    print(f"   Dict keys: {list(raw_data.keys())}")
                    
                    # Look for data in common keys
                    if 'data' in raw_data:
                        data = raw_data['data']
                        print(f"   Found 'data' key with {len(data)} items")
                        if data:
                            print(f"   First item dataType: {data[0].get('dataType')}")
                    elif 'items' in raw_data:
                        items = raw_data['items']
                        print(f"   Found 'items' key with {len(items)} items")
                        if items:
                            print(f"   First item dataType: {items[0].get('dataType')}")
                    else:
                        print(f"   No 'data' or 'items' key found")
                        print(f"   Available keys: {list(raw_data.keys())}")
                
                else:
                    print(f"   Unexpected type: {type(raw_data)}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_scrape())
