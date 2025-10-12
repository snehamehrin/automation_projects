#!/usr/bin/env python3
"""
Test script to process one URL and write to brand_reddit_posts_comments table
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


async def test_process_one_url():
    """Process one URL and write to database."""
    print("🚀 Test: Process One URL and Write to Database")
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
            print("   Please run the Google search script first")
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
                "maxComments": 100,  # Get up to 100 comments for testing
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
            
            if response.status_code in [200, 201]:  # Both 200 and 201 are success codes
                reddit_data = response.json()
                print(f"✅ Successfully scraped {len(reddit_data)} items")
                
                # Process the data
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
                            'number_of_replies': item.get('numberOfreplies', 0),  # Use the correct field name
                            'data_type': 'comment',
                            'brand_name': brand_name
                        }
                        processed_data.append(processed_item)
                
                print(f"📊 Processed {len(processed_data)} items:")
                posts = [item for item in processed_data if item['data_type'] == 'post']
                comments = [item for item in processed_data if item['data_type'] == 'comment']
                print(f"   Posts: {len(posts)}")
                print(f"   Comments: {len(comments)}")
                
                # Save to database
                print(f"\n💾 Saving to brand_reddit_posts_comments table...")
                print(f"   Attempting to insert {len(processed_data)} items")
                
                # Show what we're about to insert
                print(f"\n🔍 Data to be inserted:")
                for i, item in enumerate(processed_data[:2], 1):
                    print(f"   {i}. {item['data_type']} - {item['brand_name']}")
                    print(f"      URL: {item['url']}")
                    print(f"      Community: {item['community_name']}")
                    print(f"      Upvotes: {item['up_votes']}")
                    print(f"      Number of replies: {item['number_of_replies']}")
                    print(f"      Created at: {item['created_at_reddit']}")
                    print()
                
                if len(processed_data) > 2:
                    print(f"   ... and {len(processed_data) - 2} more items")
                
                try:
                    print(f"   📡 Calling Supabase insert...")
                    response = supabase.table('brand_reddit_posts_comments').insert(processed_data).execute()
                    
                    print(f"   📊 Insert response status: {response}")
                    print(f"   📊 Response data: {response.data}")
                    print(f"   📊 Response count: {response.count}")
                    
                    if response.data:
                        print(f"✅ Successfully saved {len(response.data)} items to database")
                        
                        # Show sample of saved data
                        print(f"\n📄 Sample saved data:")
                        for i, item in enumerate(response.data[:3], 1):
                            print(f"   {i}. {item['data_type']} - {item['brand_name']}")
                            print(f"      ID: {item['id']}")
                            print(f"      Community: {item['community_name']}")
                            print(f"      Upvotes: {item['up_votes']}")
                            print()
                        
                        if len(response.data) > 3:
                            print(f"   ... and {len(response.data) - 3} more items")
                        
                        # Mark the URL as processed in brand_google_reddit table
                        print(f"\n🏷️  Marking URL as processed in brand_google_reddit table...")
                        try:
                            print(f"   📡 Updating URL ID: {url_data['id']}")
                            update_response = supabase.table('brand_google_reddit').update({
                                'processed': True
                            }).eq('id', url_data['id']).execute()
                            
                            print(f"   📊 Update response: {update_response}")
                            print(f"   📊 Update data: {update_response.data}")
                            
                            if update_response.data:
                                print(f"✅ Successfully marked URL as processed")
                                print(f"   URL ID: {url_data['id']}")
                                print(f"   Title: {url_data['title']}")
                            else:
                                print("❌ Failed to mark URL as processed")
                                print("   No data returned from update")
                                
                        except Exception as e:
                            print(f"❌ Error marking URL as processed: {e}")
                            print(f"   Error type: {type(e).__name__}")
                            import traceback
                            print(f"   Traceback: {traceback.format_exc()}")
                        
                    else:
                        print("❌ No data returned from database insert")
                        print("   This might indicate a permission issue or constraint violation")
                        
                except Exception as e:
                    print(f"❌ Error saving to database: {e}")
                    print(f"   Error type: {type(e).__name__}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    
                    # Check for specific error types
                    if "permission" in str(e).lower():
                        print("   💡 This looks like a permission issue.")
                        print("   Make sure your Supabase key has INSERT permissions on this table.")
                    elif "constraint" in str(e).lower():
                        print("   💡 This looks like a constraint violation.")
                        print("   Check if the data_type values are 'post' or 'comment' only.")
                    elif "relation" in str(e).lower():
                        print("   💡 The table might not exist.")
                        print("   Make sure 'brand_reddit_posts_comments' table exists in your database.")
                
            else:
                print(f"❌ Error scraping Reddit: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception during scraping: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Full traceback:")
            print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_process_one_url())
