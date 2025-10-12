#!/usr/bin/env python3
"""
Test script to just test writing to brand_reddit_posts_comments table
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client


def test_db_write():
    """Test writing sample data to brand_reddit_posts_comments table."""
    print("🧪 Test: Write Sample Data to Database")
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
    
    # Create sample data
    sample_data = [
        {
            'url': 'https://reddit.com/r/test/comments/abc123/test_post/',
            'post_id': 'abc123',
            'parent_id': None,
            'category': 'post',
            'community_name': 'test',
            'created_at_reddit': '2024-01-15T10:30:00Z',
            'scraped_at': datetime.now().isoformat(),
            'up_votes': 25,
            'number_of_replies': 5,
            'data_type': 'post',
            'brand_name': 'TestBrand'
        },
        {
            'url': 'https://reddit.com/r/test/comments/abc123/test_post/def456/',
            'post_id': 'abc123',
            'parent_id': 'abc123',
            'category': 'comment',
            'community_name': 'test',
            'created_at_reddit': '2024-01-15T11:00:00Z',
            'scraped_at': datetime.now().isoformat(),
            'up_votes': 10,
            'number_of_replies': 0,
            'data_type': 'comment',
            'brand_name': 'TestBrand'
        }
    ]
    
    print(f"📊 Sample data to insert:")
    for i, item in enumerate(sample_data, 1):
        print(f"   {i}. {item['data_type']} - {item['brand_name']}")
        print(f"      URL: {item['url']}")
        print(f"      Community: {item['community_name']}")
        print(f"      Upvotes: {item['up_votes']}")
        print()
    
    # Try to insert
    print(f"💾 Attempting to insert {len(sample_data)} items...")
    try:
        response = supabase.table('brand_reddit_posts_comments').insert(sample_data).execute()
        
        if response.data:
            print(f"✅ Successfully inserted {len(response.data)} items!")
            print(f"📄 Inserted data:")
            for i, item in enumerate(response.data, 1):
                print(f"   {i}. ID: {item['id']}")
                print(f"      Data Type: {item['data_type']}")
                print(f"      Brand: {item['brand_name']}")
                print(f"      Community: {item['community_name']}")
                print(f"      Upvotes: {item['up_votes']}")
                print()
        else:
            print("❌ No data returned from insert")
            print("   This might indicate a permission issue or table constraint violation")
            
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if it's a permission issue
        if "permission" in str(e).lower():
            print("   💡 This looks like a permission issue.")
            print("   Make sure your Supabase key has INSERT permissions on this table.")
        elif "constraint" in str(e).lower():
            print("   💡 This looks like a constraint violation.")
            print("   Check if the data_type values are 'post' or 'comment' only.")
        elif "relation" in str(e).lower():
            print("   💡 The table might not exist.")
            print("   Make sure 'brand_reddit_posts_comments' table exists in your database.")


if __name__ == "__main__":
    test_db_write()
