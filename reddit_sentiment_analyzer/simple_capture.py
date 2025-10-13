#!/usr/bin/env python3
"""
Simple script to capture raw Apify response and save it
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


async def capture_data():
    """Capture raw Apify response and save it."""
    print("🚀 Simple Data Capture")
    print("=" * 40)
    
    # Get credentials
    apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not apify_token:
        print("❌ APIFY_API_KEY not found")
        return
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE credentials not found")
        return
    
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
        print(f"   Brand: {url_data['brand_name']}")
        
    except Exception as e:
        print(f"❌ Error getting URL: {e}")
        return
    
    # Scrape with Apify
    print(f"\n📡 Scraping with Apify...")
    
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
            
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                # Get the raw response
                raw_data = response.json()
                
                print(f"✅ Got response!")
                print(f"   Type: {type(raw_data)}")
                
                if isinstance(raw_data, dict):
                    print(f"   Keys: {list(raw_data.keys())}")
                    if 'data' in raw_data:
                        print(f"   Data length: {len(raw_data['data'])}")
                    if 'items' in raw_data:
                        print(f"   Items length: {len(raw_data['items'])}")
                elif isinstance(raw_data, list):
                    print(f"   List length: {len(raw_data)}")
                
                # Save raw response
                results_dir = Path("results")
                results_dir.mkdir(exist_ok=True)
                
                filename = results_dir / f"raw_apify_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'source_url': url_data['url'],
                        'brand_name': url_data['brand_name'],
                        'scraped_at': datetime.now().isoformat(),
                        'raw_response': raw_data,
                        'response_type': str(type(raw_data)),
                        'response_keys': list(raw_data.keys()) if isinstance(raw_data, dict) else None,
                        'response_length': len(raw_data) if isinstance(raw_data, (list, dict)) else None
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"\n💾 Raw response saved to: {filename}")
                
                # Show sample data
                if isinstance(raw_data, list) and raw_data:
                    print(f"\n📄 Sample item:")
                    sample = raw_data[0]
                    print(f"   Keys: {list(sample.keys())}")
                    print(f"   DataType: {sample.get('dataType')}")
                    print(f"   Body: {sample.get('body', '')[:100]}...")
                elif isinstance(raw_data, dict):
                    if 'data' in raw_data and raw_data['data']:
                        print(f"\n📄 Sample item from 'data' key:")
                        sample = raw_data['data'][0]
                        print(f"   Keys: {list(sample.keys())}")
                        print(f"   DataType: {sample.get('dataType')}")
                        print(f"   Body: {sample.get('body', '')[:100]}...")
                    elif 'items' in raw_data and raw_data['items']:
                        print(f"\n📄 Sample item from 'items' key:")
                        sample = raw_data['items'][0]
                        print(f"   Keys: {list(sample.keys())}")
                        print(f"   DataType: {sample.get('dataType')}")
                        print(f"   Body: {sample.get('body', '')[:100]}...")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(capture_data())
