#!/usr/bin/env python3
"""
Test each step of the workflow individually
"""

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Get credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

def test_step_1_prospect_search():
    """Test Step 1: Search for prospects"""
    print("🔍 Step 1: Testing prospect search...")
    
    # Test searching for "Knix"
    response = supabase.table('prospects').select('*').ilike('brand_name', '%Knix%').execute()
    
    if response.data:
        print(f"✅ Found {len(response.data)} prospects matching 'Knix':")
        for prospect in response.data:
            print(f"   - {prospect.get('brand_name')} (ID: {prospect.get('id')})")
        return response.data[0]  # Return first match
    else:
        print("❌ No prospects found for 'Knix'")
        return None

def test_step_2_check_tables():
    """Test Step 2: Check if prospect_id columns exist"""
    print("\n🔍 Step 2: Testing if prospect_id columns exist...")
    
    tables_to_check = [
        'google_results',
        'brand_google_reddit', 
        'brand_reddit_posts_comments',
        'reddit_brand_analysis_results'
    ]
    
    for table in tables_to_check:
        try:
            # Try to select prospect_id column
            response = supabase.table(table).select('prospect_id').limit(1).execute()
            print(f"✅ {table}: prospect_id column exists")
        except Exception as e:
            print(f"❌ {table}: prospect_id column missing - {e}")

def test_step_3_check_existing_data():
    """Test Step 3: Check existing data in tables"""
    print("\n🔍 Step 3: Checking existing data...")
    
    # Check brand_reddit_posts_comments
    response = supabase.table('brand_reddit_posts_comments').select('*').limit(3).execute()
    if response.data:
        print(f"✅ brand_reddit_posts_comments: {len(response.data)} records found")
        sample = response.data[0]
        print(f"   Sample record has prospect_id: {'prospect_id' in sample}")
        print(f"   Brand: {sample.get('brand_name')}")
    else:
        print("❌ No data in brand_reddit_posts_comments")
    
    # Check brand_google_reddit
    response = supabase.table('brand_google_reddit').select('*').limit(3).execute()
    if response.data:
        print(f"✅ brand_google_reddit: {len(response.data)} records found")
        sample = response.data[0]
        print(f"   Sample record has prospect_id: {'prospect_id' in sample}")
        print(f"   Brand: {sample.get('brand_name')}")
    else:
        print("❌ No data in brand_google_reddit")

def test_step_4_update_prospect_id():
    """Test Step 4: Update a record with prospect_id"""
    print("\n🔍 Step 4: Testing prospect_id update...")
    
    # Get a prospect
    prospect = test_step_1_prospect_search()
    if not prospect:
        print("❌ No prospect found to test with")
        return
    
    prospect_id = prospect.get('id')
    brand_name = prospect.get('brand_name')
    
    print(f"Using prospect: {brand_name} (ID: {prospect_id})")
    
    # Try to update a record in brand_reddit_posts_comments
    try:
        response = supabase.table('brand_reddit_posts_comments').select('*').eq('brand_name', brand_name).limit(1).execute()
        
        if response.data:
            record = response.data[0]
            record_id = record.get('id')
            
            # Update with prospect_id
            update_response = supabase.table('brand_reddit_posts_comments').update({
                'prospect_id': prospect_id
            }).eq('id', record_id).execute()
            
            if update_response.data:
                print(f"✅ Successfully updated record {record_id} with prospect_id: {prospect_id}")
            else:
                print("❌ Failed to update record")
        else:
            print(f"❌ No records found for brand: {brand_name}")
            
    except Exception as e:
        print(f"❌ Error updating record: {e}")

def main():
    """Run all test steps"""
    print("🧪 Testing Sentiment Analysis Workflow - Step by Step")
    print("=" * 60)
    
    test_step_1_prospect_search()
    test_step_2_check_tables()
    test_step_3_check_existing_data()
    test_step_4_update_prospect_id()
    
    print("\n🎉 Step-by-step testing complete!")

if __name__ == "__main__":
    main()
