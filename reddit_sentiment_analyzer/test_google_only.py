#!/usr/bin/env python3
"""
Test only the Google search part of the workflow
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import httpx


async def test_google_search():
    """Test Google search with site:reddit.com"""
    print("🔍 Testing Google Search with site:reddit.com")
    print("=" * 60)
    
    # Get Apify token
    apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
    if not apify_token:
        print("❌ APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
        return
    
    print(f"🔑 Token: {apify_token[:10]}...")
    
    # Get brand name
    brand_name = input("Enter brand name to test: ").strip()
    if not brand_name:
        brand_name = "Apple"
    
    print(f"🎯 Testing with brand: {brand_name}")
    
    # Create search queries (following N8N workflow)
    queries = [
        f"site:reddit.com {brand_name} review",
        f"site:reddit.com {brand_name} reviews"
    ]
    
    print(f"\n📡 Search queries:")
    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query}")
    
    all_results = []
    reddit_urls = []
    
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Search {i}/{len(queries)}: '{query}'")
            print("-" * 50)
            
            try:
                payload = {
                    "queries": query,
                    "resultsPerPage": 20,
                    "maxPagesPerQuery": 1,
                    "aiMode": "aiModeOff"
                }
                
                print("📡 Calling Apify Google Search Scraper...")
                print(f"   Payload: {json.dumps(payload, indent=2)}")
                
                response = await client.post(
                    "https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                    headers={"Authorization": f"Bearer {apify_token}"},
                    json=payload,
                    timeout=60.0
                )
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code in [200, 201]:  # Both 200 and 201 are success
                    results = response.json()
                    print(f"✅ Success! Found {len(results)} search results")
                    
                    # Show first few results
                    for j, result in enumerate(results[:5], 1):
                        print(f"\n   {j}. {result.get('title', 'No title')}")
                        print(f"      URL: {result.get('url', 'No URL')}")
                        print(f"      Description: {result.get('description', 'No description')[:100]}...")
                        
                        # Check if it's a Reddit URL
                        if result.get('url') and 'reddit.com' in result['url']:
                            reddit_urls.append({
                                'url': result['url'],
                                'title': result.get('title', ''),
                                'description': result.get('description', '')
                            })
                            print(f"      🎯 REDDIT URL FOUND!")
                    
                    all_results.extend(results)
                    
                    if len(results) > 5:
                        print(f"   ... and {len(results) - 5} more results")
                        
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                continue
    
    # Summary
    print(f"\n📊 Search Summary")
    print("=" * 30)
    print(f"✅ Total search results: {len(all_results)}")
    print(f"🎯 Reddit URLs found: {len(reddit_urls)}")
    
    if reddit_urls:
        print(f"\n🔗 Reddit URLs found:")
        for i, url_data in enumerate(reddit_urls, 1):
            print(f"   {i}. {url_data['url']}")
            print(f"      Title: {url_data['title']}")
    
    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Save all search results
    google_file = results_dir / f"google_search_{brand_name.lower().replace(' ', '_')}.json"
    with open(google_file, 'w', encoding='utf-8') as f:
        json.dump({
            'brand_name': brand_name,
            'queries': queries,
            'all_results': all_results,
            'reddit_urls': reddit_urls,
            'summary': {
                'total_results': len(all_results),
                'reddit_urls_found': len(reddit_urls)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {google_file}")
    
    if reddit_urls:
        print(f"\n🎉 Google search is working! Found {len(reddit_urls)} Reddit URLs.")
        print("   Next step: Use these URLs to scrape Reddit posts and comments.")
    else:
        print(f"\n⚠️  No Reddit URLs found. This might be normal for some brands.")
        print("   Try a different brand name or check if the brand has Reddit discussions.")


if __name__ == "__main__":
    asyncio.run(test_google_search())
