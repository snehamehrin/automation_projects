#!/usr/bin/env python3
"""
Test Apify integration - Google Search and Reddit Scraper
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


class ApifyTester:
    """Test Apify API integration."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.apify_base_url = "https://api.apify.com/v2"
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
        
        print(f"🔑 Apify Token: {self.apify_token[:10]}...")
    
    async def test_google_search(self, brand_name: str):
        """Test Google search using Apify."""
        print(f"\n🔍 Testing Google Search for '{brand_name}'")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            try:
                # Use Apify Google Search Scraper with site:reddit.com
                # Following N8N workflow pattern
                queries = [
                    f"site:reddit.com {brand_name} review",
                    f"site:reddit.com {brand_name} reviews"
                ]
                
                payload = {
                    "queries": "\n".join(queries),
                    "resultsPerPage": 10,
                    "maxPagesPerQuery": 1,
                    "aiMode": "aiModeOff"
                }
                
                print("📡 Calling Apify Google Search Scraper...")
                print(f"   Query: {payload['queries']}")
                
                response = await client.post(
                    f"{self.apify_base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    json=payload,
                    timeout=60.0
                )
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Success! Found {len(results)} search results")
                    
                    # Show first few results
                    for i, result in enumerate(results[:3], 1):
                        print(f"\n   {i}. {result.get('title', 'No title')}")
                        print(f"      URL: {result.get('url', 'No URL')}")
                        print(f"      Description: {result.get('description', 'No description')[:100]}...")
                    
                    # Save results to file
                    filename = f"google_search_{brand_name.lower().replace(' ', '_')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    print(f"💾 Results saved to: {filename}")
                    
                    return results
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return []
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                return []
    
    async def test_reddit_search(self, brand_name: str):
        """Test Reddit search using Apify."""
        print(f"\n🔍 Testing Reddit Search for '{brand_name}'")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            try:
                # Use Apify Reddit Scraper
                payload = {
                    "searchTerms": [f"{brand_name}", f"{brand_name} review"],
                    "maxItems": 10,
                    "searchComments": True,
                    "searchPosts": True,
                    "sort": "relevance"
                }
                
                print("📡 Calling Apify Reddit Scraper...")
                print(f"   Search terms: {payload['searchTerms']}")
                
                response = await client.post(
                    f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    json=payload,
                    timeout=60.0
                )
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Success! Found {len(results)} Reddit posts")
                    
                    # Show first few results
                    for i, result in enumerate(results[:3], 1):
                        print(f"\n   {i}. {result.get('title', 'No title')}")
                        print(f"      Subreddit: r/{result.get('subreddit', 'unknown')}")
                        print(f"      Score: {result.get('score', 0)}")
                        print(f"      Text: {result.get('text', 'No text')[:100]}...")
                    
                    # Save results to file
                    filename = f"reddit_search_{brand_name.lower().replace(' ', '_')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    print(f"💾 Results saved to: {filename}")
                    
                    return results
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return []
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                return []
    
    async def test_reddit_workflow(self, brand_name: str):
        """Test the complete Reddit workflow following N8N pattern."""
        print(f"\n🔍 Testing Complete Reddit Workflow for '{brand_name}'")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            try:
                # Step 1: Google Search with site:reddit.com
                print("📡 Step 1: Google Search for Reddit URLs...")
                queries = [
                    f"site:reddit.com {brand_name} review",
                    f"site:reddit.com {brand_name} reviews"
                ]
                
                reddit_urls = []
                for query in queries:
                    payload = {
                        "queries": query,
                        "resultsPerPage": 10,
                        "maxPagesPerQuery": 1,
                        "aiMode": "aiModeOff"
                    }
                    
                    response = await client.post(
                        f"{self.apify_base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                        headers={"Authorization": f"Bearer {self.apify_token}"},
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        google_results = response.json()
                        for result in google_results:
                            if result.get('url') and 'reddit.com/r/' in result['url']:
                                reddit_urls.append({
                                    'url': result['url'],
                                    'title': result.get('title', ''),
                                    'description': result.get('description', '')
                                })
                
                print(f"✅ Found {len(reddit_urls)} Reddit URLs")
                
                if not reddit_urls:
                    print("❌ No Reddit URLs found")
                    return []
                
                # Step 2: Scrape Reddit posts using URLs
                print("📡 Step 2: Scraping Reddit posts...")
                all_reddit_data = []
                
                for i, reddit_url in enumerate(reddit_urls[:3]):  # Test with first 3 URLs
                    print(f"   Scraping {i+1}/{min(len(reddit_urls), 3)}: {reddit_url['url']}")
                    
                    payload = {
                        "startUrls": [{"url": reddit_url['url']}],
                        "maxPosts": 1,
                        "maxComments": 10,
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
                        reddit_data = response.json()
                        all_reddit_data.extend(reddit_data)
                        print(f"   Found {len(reddit_data)} items")
                    else:
                        print(f"   ❌ Error: {response.status_code}")
                
                print(f"✅ Total Reddit data collected: {len(all_reddit_data)} items")
                
                # Save results
                filename = f"reddit_workflow_{brand_name.lower().replace(' ', '_')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'reddit_urls': reddit_urls,
                        'reddit_data': all_reddit_data,
                        'summary': {
                            'total_urls': len(reddit_urls),
                            'total_items': len(all_reddit_data),
                            'posts': len([item for item in all_reddit_data if item.get('dataType') == 'post']),
                            'comments': len([item for item in all_reddit_data if item.get('dataType') == 'comment'])
                        }
                    }, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {filename}")
                
                return all_reddit_data
                
            except Exception as e:
                print(f"❌ Reddit workflow failed: {e}")
                return []
    
    async def test_apify_account(self):
        """Test Apify account access."""
        print("🔍 Testing Apify Account Access")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.apify_base_url}/users/me",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    timeout=30.0
                )
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    user_info = response.json()
                    print("✅ Account access successful!")
                    print(f"   Username: {user_info.get('username', 'Unknown')}")
                    print(f"   Email: {user_info.get('email', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Account access failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                return False


async def main():
    """Main test function."""
    print("🚀 Apify Integration Test")
    print("=" * 60)
    
    try:
        # Initialize tester
        tester = ApifyTester()
        
        # Test account access
        account_ok = await tester.test_apify_account()
        
        if not account_ok:
            print("\n❌ Account test failed. Please check your APIFY_TOKEN.")
            return
        
        # Get brand name from user
        brand_name = input("\nEnter brand name to test: ").strip()
        if not brand_name:
            brand_name = "Apple"  # Default test brand
        
        print(f"\n🎯 Testing with brand: {brand_name}")
        
        # Test Google search
        google_results = await tester.test_google_search(brand_name)
        
        # Test Reddit search (following N8N workflow)
        reddit_results = await tester.test_reddit_workflow(brand_name)
        
        # Create results directory
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save summary
        summary = {
            "brand_name": brand_name,
            "timestamp": datetime.now().isoformat(),
            "account_access": account_ok,
            "google_search_results": len(google_results),
            "reddit_search_results": len(reddit_results),
            "files_created": []
        }
        
        # Move files to results directory
        if google_results:
            google_file = f"google_search_{brand_name.lower().replace(' ', '_')}.json"
            if Path(google_file).exists():
                new_path = results_dir / google_file
                Path(google_file).rename(new_path)
                summary["files_created"].append(str(new_path))
        
        if reddit_results:
            reddit_file = f"reddit_search_{brand_name.lower().replace(' ', '_')}.json"
            if Path(reddit_file).exists():
                new_path = results_dir / reddit_file
                Path(reddit_file).rename(new_path)
                summary["files_created"].append(str(new_path))
        
        # Save summary
        summary_file = results_dir / f"test_summary_{brand_name.lower().replace(' ', '_')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 30)
        print(f"✅ Account access: {'Working' if account_ok else 'Failed'}")
        print(f"🔍 Google search: {len(google_results)} results")
        print(f"🔍 Reddit search: {len(reddit_results)} results")
        print(f"💾 Files saved to: results/ directory")
        print(f"📄 Summary saved to: {summary_file}")
        
        if google_results or reddit_results:
            print("\n🎉 Apify integration is working!")
        else:
            print("\n⚠️  No results found. This might be normal for some brands.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
