#!/usr/bin/env python3
"""
Check if brand_reddit_posts_comments table exists and show its structure
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


def check_table_exists():
    """Check if brand_reddit_posts_comments table exists and show its structure."""
    print("🔍 Checking brand_reddit_posts_comments table")
    print("=" * 60)
    
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
        # Try to get table info by selecting one record
        print(f"\n📡 Testing table access...")
        response = supabase.table('brand_reddit_posts_comments').select('*').limit(1).execute()
        
        print(f"✅ Table exists and is accessible!")
        print(f"📊 Response: {response}")
        print(f"📊 Data: {response.data}")
        print(f"📊 Count: {response.count}")
        
        if response.data:
            print(f"\n📋 Table structure (from first record):")
            first_record = response.data[0]
            for column, value in first_record.items():
                print(f"   {column}: {type(value).__name__} = {value}")
        else:
            print(f"\n📭 Table is empty (no records)")
            
        # Try to get count
        print(f"\n📊 Getting total count...")
        count_response = supabase.table('brand_reddit_posts_comments').select('id', count='exact').execute()
        print(f"📊 Total records: {count_response.count}")
        
    except Exception as e:
        print(f"❌ Error accessing table: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("   💡 The 'brand_reddit_posts_comments' table doesn't exist yet.")
            print("   Please create it with this SQL:")
            print("""
    create table public.brand_reddit_posts_comments (
      id uuid not null default gen_random_uuid (),
      url text not null,
      post_id text null,
      parent_id text null,
      category text null,
      community_name text null,
      created_at_reddit text null,
      scraped_at timestamp with time zone null default now(),
      up_votes integer null default 0,
      number_of_replies integer null default 0,
      data_type text not null,
      brand_name text not null,
      constraint reddit_posts_comments_pkey primary key (id),
      constraint brand_reddit_posts_comments_data_type_check check (
        (
          data_type = any (array['post'::text, 'comment'::text])
        )
      )
    ) TABLESPACE pg_default;
            """)
        elif "permission" in str(e).lower():
            print("   💡 This looks like a permission issue.")
            print("   Make sure your Supabase key has SELECT permissions on this table.")


if __name__ == "__main__":
    check_table_exists()
