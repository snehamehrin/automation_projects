#!/usr/bin/env python3
"""
Final working Reddit scraper - no bullshit
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
import httpx

# Get credentials
apify_token = os.getenv("APIFY_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

async def main():
    print("🚀 Final Working Scraper")
    
    # Get one URL
    response = supabase.table('brand_google_reddit').select('*').eq('processed', False).limit(1).execute()
    
    if not response.data:
        print("No URLs found")
        return
    
    url_data = response.data[0]
    print(f"Scraping: {url_data['title']}")
    
    # Scrape with Apify
    async with httpx.AsyncClient() as client:
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
        
        if response.status_code == 200:
            data = response.json()
            print(f"Got {len(data)} items")
            
            # Process data
            processed = []
            for item in data:
                if item.get('dataType') == 'post':
                    processed.append({
                        'url': item.get('url', ''),
                        'post_id': item.get('id', ''),
                        'parent_id': None,
                        'category': 'post',
                        'community_name': item.get('communityName', ''),
                        'created_at_reddit': item.get('createdAt', ''),
                        'scraped_at': datetime.now().isoformat(),
                        'up_votes': item.get('upVotes', 0),
                        'number_of_replies': item.get('numberOfReplies', 0),
                        'data_type': 'post',
                        'brand_name': url_data['brand_name'],
                        'body': f"{item.get('title', '')}. {item.get('body', '')}".strip()
                    })
                elif item.get('dataType') == 'comment':
                    processed.append({
                        'url': item.get('url', ''),
                        'post_id': item.get('postId', ''),
                        'parent_id': item.get('parentId', ''),
                        'category': 'comment',
                        'community_name': item.get('communityName', ''),
                        'created_at_reddit': item.get('createdAt', ''),
                        'scraped_at': datetime.now().isoformat(),
                        'up_votes': item.get('upVotes', 0),
                        'number_of_replies': item.get('numberOfReplies', 0),
                        'data_type': 'comment',
                        'brand_name': url_data['brand_name'],
                        'body': item.get('body', '')
                    })
            
            print(f"Processed {len(processed)} items")
            
            # Save to database
            if processed:
                result = supabase.table('brand_reddit_posts_comments').insert(processed).execute()
                print(f"✅ Saved {len(result.data)} items to database")
                
                # Mark as processed
                supabase.table('brand_google_reddit').update({'processed': True}).eq('id', url_data['id']).execute()
                print("✅ Marked URL as processed")
        else:
            print(f"Error: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
