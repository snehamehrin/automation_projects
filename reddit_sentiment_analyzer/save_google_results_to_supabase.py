#!/usr/bin/env python3
"""
Save Google search results to Supabase database
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


class GoogleResultsToSupabase:
    """Save Google search results to Supabase."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.apify_base_url = "https://api.apify.com/v2"
    
    async def search_and_save(self, brand_name: str):
        """Search Google and save results to Supabase."""
        print(f"🔍 Searching Google for Reddit posts about '{brand_name}'")
        print("=" * 60)
        
        # Create search queries
        queries = [
            f"site:reddit.com {brand_name} review",
            f"site:reddit.com {brand_name} reviews"
        ]
        
        all_results = []
        
        async with httpx.AsyncClient() as client:
            for i, query in enumerate(queries, 1):
                print(f"\n📡 Search {i}/{len(queries)}: '{query}'")
                
                try:
                    payload = {
                        "queries": query,
                        "resultsPerPage": 20,
                        "maxPagesPerQuery": 1,
                        "aiMode": "aiModeOff"
                    }
                    
                    response = await client.post(
                        f"{self.apify_base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                        headers={"Authorization": f"Bearer {self.apify_token}"},
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code in [200, 201]:
                        results = response.json()
                        print(f"✅ Found {len(results)} results")
                        
                        # Process results
                        for result in results:
                            if result.get('organicResults'):
                                for organic in result['organicResults']:
                                    if organic.get('url') and 'reddit.com' in organic['url']:
                                        formatted_result = self._format_result(organic, brand_name, query)
                                        all_results.append(formatted_result)
                                        print(f"   🎯 Reddit URL: {organic.get('title', 'No title')[:50]}...")
                    else:
                        print(f"❌ Error: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Exception: {e}")
                    continue
        
        print(f"\n📊 Total Reddit results found: {len(all_results)}")
        
        if not all_results:
            print("❌ No Reddit results found to save")
            return
        
        # Save to Supabase
        await self._save_to_supabase(all_results, brand_name)
    
    def _format_result(self, organic_result: dict, brand_name: str, search_query: str) -> dict:
        """Format Google search result for Supabase brand_google_reddit table."""
        # Parse comments amount to integer
        comments_text = organic_result.get('commentsAmount', '')
        comments_amount = None
        if comments_text:
            # Extract number from strings like "40+ comments", "7 comments", "10+ comments"
            import re
            numbers = re.findall(r'\d+', comments_text)
            if numbers:
                comments_amount = int(numbers[0])
        
        # Parse last_updated to date
        last_updated = None
        last_updated_text = organic_result.get('lastUpdated', '')
        if last_updated_text:
            # Handle formats like "4 years ago", "6 months ago", "2 years ago"
            # For now, we'll set it to None since we can't easily parse relative dates
            # You might want to implement a more sophisticated date parser
            pass
        
        return {
            'title': organic_result.get('title', ''),
            'brand_name': brand_name,
            'url': organic_result.get('url', ''),
            'description': organic_result.get('description', ''),
            'emphasized_keywords': organic_result.get('emphasizedKeywords', []),  # Already a list
            'comments_amount': comments_amount,
            'last_updated': last_updated,
            'extrated_at': datetime.now().date().isoformat()  # Today's date
        }
    
    async def _save_to_supabase(self, results: list, brand_name: str):
        """Save results to Supabase."""
        print(f"\n💾 Saving {len(results)} results to Supabase...")
        
        try:
            # Insert results
            response = self.supabase.table('brand_google_reddit').insert(results).execute()
            
            if response.data:
                print(f"✅ Successfully saved {len(response.data)} results to Supabase")
                
                # Show summary
                print(f"\n📋 Summary:")
                print(f"   Brand: {brand_name}")
                print(f"   Results saved: {len(response.data)}")
                print(f"   Table: brand_google_reddit")
                
                # Show first few results
                print(f"\n📄 Sample results:")
                for i, result in enumerate(response.data[:3], 1):
                    print(f"   {i}. {result.get('title', 'No title')[:60]}...")
                    print(f"      URL: {result.get('url', 'No URL')}")
                    print(f"      Comments: {result.get('comments_amount', 'No comments')}")
                    print()
                
            else:
                print("❌ No data returned from Supabase insert")
                
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            print("   Make sure the 'brand_google_reddit' table exists in your Supabase database")
    
    def create_table_sql(self):
        """Return SQL to create the google_search_results table."""
        return """
        CREATE TABLE google_search_results (
            id BIGSERIAL PRIMARY KEY,
            brand_name TEXT NOT NULL,
            search_query TEXT NOT NULL,
            title TEXT,
            url TEXT NOT NULL,
            reddit BOOLEAN DEFAULT TRUE,
            description TEXT,
            emphasized_keywords JSONB,
            comments TEXT,
            last_updated TEXT,
            type TEXT,
            position INTEGER,
            displayed_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create index for faster queries
        CREATE INDEX idx_google_search_results_brand_name ON google_search_results(brand_name);
        CREATE INDEX idx_google_search_results_url ON google_search_results(url);
        CREATE INDEX idx_google_search_results_created_at ON google_search_results(created_at);
        """


async def main():
    """Main function."""
    print("🚀 Google Search Results to Supabase")
    print("=" * 60)
    
    try:
        # Initialize
        saver = GoogleResultsToSupabase()
        
        # Get brand name
        brand_name = input("Enter brand name to search and save: ").strip()
        if not brand_name:
            brand_name = "Knix"
        
        print(f"🎯 Brand: {brand_name}")
        
        # Check if table exists
        try:
            test_response = saver.supabase.table('brand_google_reddit').select('id').limit(1).execute()
            print("✅ Table 'brand_google_reddit' exists")
        except Exception as e:
            print("❌ Table 'brand_google_reddit' does not exist")
            print("\n📋 Please create the table in your Supabase SQL Editor:")
            print("""
            create table public.brand_google_reddit (
              id uuid not null default gen_random_uuid (),
              created_at timestamp with time zone null default now(),
              updated_at timestamp with time zone null default now(),
              title text not null,
              brand_name text not null,
              url text not null,
              description text null,
              emphasized_keywords text[] null default '{}'::text[],
              comments_amount integer null,
              last_updated date null,
              extrated_at date null,
              constraint brand_google_reddit_pkey primary key (id)
            ) TABLESPACE pg_default;
            """)
            return
        
        # Search and save
        await saver.search_and_save(brand_name)
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
