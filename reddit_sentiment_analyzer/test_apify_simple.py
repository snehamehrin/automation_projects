#!/usr/bin/env python3
"""
Simple Apify test - asks for token directly
"""

import asyncio
import httpx


async def test_apify_with_token():
    """Test Apify with token input."""
    print("🚀 Simple Apify Test")
    print("=" * 40)
    
    # Get Apify token from user
    apify_token = input("Enter your Apify token: ").strip()
    
    if not apify_token:
        print("❌ No token provided!")
        return
    
    print(f"🔑 Token: {apify_token[:10]}...")
    
    # Get brand name
    brand_name = input("Enter brand name to test: ").strip()
    if not brand_name:
        brand_name = "Apple"
    
    print(f"🎯 Testing with brand: {brand_name}")
    
    # Test account access
    print("\n🔍 Testing account access...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.apify.com/v2/users/me",
                headers={"Authorization": f"Bearer {apify_token}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                user_info = response.json()
                print("✅ Account access successful!")
                print(f"   Username: {user_info.get('username', 'Unknown')}")
            else:
                print(f"❌ Account access failed: {response.status_code}")
                return
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return
    
    # Test Google search
    print(f"\n🔍 Testing Google search for '{brand_name}'...")
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "queries": [f"{brand_name} review"],
                "maxResultsPerQuery": 5,
                "resultsType": "organic"
            }
            
            response = await client.post(
                "https://api.apify.com/v2/acts/google-search-scraper~google-search-scraper/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Google search successful! Found {len(results)} results")
                
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. {result.get('title', 'No title')}")
                    print(f"      URL: {result.get('url', 'No URL')}")
            else:
                print(f"❌ Google search failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Google search error: {e}")
    
    # Test Reddit search
    print(f"\n🔍 Testing Reddit search for '{brand_name}'...")
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "searchTerms": [f"{brand_name}"],
                "maxItems": 5,
                "searchComments": True,
                "searchPosts": True,
                "sort": "relevance"
            }
            
            response = await client.post(
                "https://api.apify.com/v2/acts/reddit-scraper~reddit-scraper/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {apify_token}"},
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Reddit search successful! Found {len(results)} results")
                
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. {result.get('title', 'No title')}")
                    print(f"      Subreddit: r/{result.get('subreddit', 'unknown')}")
                    print(f"      Score: {result.get('score', 0)}")
            else:
                print(f"❌ Reddit search failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Reddit search error: {e}")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_apify_with_token())
