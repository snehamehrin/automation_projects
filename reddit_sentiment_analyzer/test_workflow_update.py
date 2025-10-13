#!/usr/bin/env python3
"""
Test the workflow by actually updating tables with prospect_id
"""

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Get credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

def search_and_select_prospect(brand_name):
    """Search for a brand and return the prospect"""
    print(f"🔍 Searching for brand: {brand_name}")
    
    # Search in prospects table
    response = supabase.table('prospects').select('*').ilike('brand_name', f'%{brand_name}%').execute()
    
    if response.data:
        prospects = response.data
        print(f"✅ Found {len(prospects)} matching prospects:")
        
        for i, prospect in enumerate(prospects, 1):
            print(f"{i}. {prospect.get('brand_name')} (ID: {prospect.get('id')})")
        
        if len(prospects) == 1:
            # Auto-select if only one match
            selected = prospects[0]
            print(f"✅ Auto-selected: {selected.get('brand_name')}")
            return selected
        else:
            # Let user choose
            try:
                choice = int(input(f"Enter choice (1-{len(prospects)}): ").strip())
                if 1 <= choice <= len(prospects):
                    return prospects[choice - 1]
                else:
                    print("❌ Invalid choice")
                    return None
            except ValueError:
                print("❌ Please enter a valid number")
                return None
    else:
        print(f"❌ No prospects found for '{brand_name}'")
        return None

def update_google_results_with_prospect_id(prospect_id, brand_name):
    """Update google_results table with prospect_id"""
    print(f"\n🔄 Updating google_results table...")
    
    try:
        # Find records matching the brand name
        response = supabase.table('google_results').select('*').ilike('brand_name', f'%{brand_name}%').execute()
        
        if response.data:
            # Update each record
            for record in response.data:
                update_response = supabase.table('google_results').update({
                    'prospect_id': prospect_id
                }).eq('id', record['id']).execute()
            
            print(f"✅ Updated {len(response.data)} records in google_results")
            return True
        else:
            print(f"📋 No records found in google_results for brand: {brand_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating google_results: {e}")
        return False

def update_brand_google_reddit_with_prospect_id(prospect_id, brand_name):
    """Update brand_google_reddit table with prospect_id"""
    print(f"🔄 Updating brand_google_reddit table...")
    
    try:
        # Find records matching the brand name
        response = supabase.table('brand_google_reddit').select('*').ilike('brand_name', f'%{brand_name}%').execute()
        
        if response.data:
            # Update each record
            for record in response.data:
                update_response = supabase.table('brand_google_reddit').update({
                    'prospect_id': prospect_id
                }).eq('id', record['id']).execute()
            
            print(f"✅ Updated {len(response.data)} records in brand_google_reddit")
            return True
        else:
            print(f"📋 No records found in brand_google_reddit for brand: {brand_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating brand_google_reddit: {e}")
        return False

def update_brand_reddit_posts_comments_with_prospect_id(prospect_id, brand_name):
    """Update brand_reddit_posts_comments table with prospect_id"""
    print(f"🔄 Updating brand_reddit_posts_comments table...")
    
    try:
        # Find records matching the brand name
        response = supabase.table('brand_reddit_posts_comments').select('*').ilike('brand_name', f'%{brand_name}%').execute()
        
        if response.data:
            # Update each record
            for record in response.data:
                update_response = supabase.table('brand_reddit_posts_comments').update({
                    'prospect_id': prospect_id
                }).eq('id', record['id']).execute()
            
            print(f"✅ Updated {len(response.data)} records in brand_reddit_posts_comments")
            return True
        else:
            print(f"📋 No records found in brand_reddit_posts_comments for brand: {brand_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating brand_reddit_posts_comments: {e}")
        return False

def verify_updates(prospect_id, brand_name):
    """Verify that the updates worked"""
    print(f"\n🔍 Verifying updates for prospect_id: {prospect_id}")
    
    tables = [
        'google_results',
        'brand_google_reddit', 
        'brand_reddit_posts_comments'
    ]
    
    for table in tables:
        try:
            response = supabase.table(table).select('*').eq('prospect_id', prospect_id).execute()
            if response.data:
                print(f"✅ {table}: {len(response.data)} records with prospect_id")
            else:
                print(f"📋 {table}: No records with prospect_id")
        except Exception as e:
            print(f"❌ {table}: Error checking - {e}")

def main():
    """Main test function"""
    print("🧪 Testing Workflow with Table Updates")
    print("=" * 50)
    
    # Use default brand name for testing
    brand_name = "Knix"  # We know this exists in prospects
    print(f"Testing with brand: {brand_name}")
    
    # Step 1: Search and select prospect
    prospect = search_and_select_prospect(brand_name)
    
    if not prospect:
        print("❌ No prospect selected. Exiting.")
        return
    
    prospect_id = prospect.get('id')
    prospect_brand_name = prospect.get('brand_name')
    
    print(f"\n✅ Selected Prospect:")
    print(f"   Brand: {prospect_brand_name}")
    print(f"   ID: {prospect_id}")
    
    # Step 2: Update all tables
    print(f"\n🔄 Updating tables with prospect_id: {prospect_id}")
    
    google_updated = update_google_results_with_prospect_id(prospect_id, prospect_brand_name)
    reddit_urls_updated = update_brand_google_reddit_with_prospect_id(prospect_id, prospect_brand_name)
    reddit_posts_updated = update_brand_reddit_posts_comments_with_prospect_id(prospect_id, prospect_brand_name)
    
    # Step 3: Verify updates
    verify_updates(prospect_id, prospect_brand_name)
    
    # Summary
    print(f"\n📊 Update Summary:")
    print(f"✅ google_results: {'Updated' if google_updated else 'No records'}")
    print(f"✅ brand_google_reddit: {'Updated' if reddit_urls_updated else 'No records'}")
    print(f"✅ brand_reddit_posts_comments: {'Updated' if reddit_posts_updated else 'No records'}")
    
    print(f"\n🎉 Test complete!")

if __name__ == "__main__":
    main()
