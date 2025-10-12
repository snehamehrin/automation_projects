#!/usr/bin/env python3
"""
Check what's in the brand_reddit_posts_comments table
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client


def check_reddit_table():
    """Check what's in the brand_reddit_posts_comments table."""
    print("🔍 Checking brand_reddit_posts_comments table")
    print("=" * 50)
    
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found")
        return
    
    # Initialize Supabase
    supabase = create_client(supabase_url, supabase_key)
    print(f"🔗 Connected to: {supabase_url}")
    
    try:
        # Get count
        count_response = supabase.table('brand_reddit_posts_comments').select('id', count='exact').execute()
        total_count = count_response.count
        print(f"📊 Total records in table: {total_count}")
        
        if total_count > 0:
            # Get recent records
            response = supabase.table('brand_reddit_posts_comments').select('*').order('scraped_at', desc=True).limit(5).execute()
            
            print(f"\n📄 Recent records:")
            for i, record in enumerate(response.data, 1):
                print(f"   {i}. ID: {record['id']}")
                print(f"      Data Type: {record['data_type']}")
                print(f"      Brand: {record['brand_name']}")
                print(f"      Community: {record['community_name']}")
                print(f"      Upvotes: {record['up_votes']}")
                print(f"      Scraped: {record['scraped_at']}")
                print()
        else:
            print("📭 Table is empty")
            
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("   💡 The 'brand_reddit_posts_comments' table doesn't exist yet.")
            print("   Please create it with the SQL you provided.")


if __name__ == "__main__":
    check_reddit_table()
