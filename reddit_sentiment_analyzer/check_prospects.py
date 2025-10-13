#!/usr/bin/env python3
"""
Check prospects table
"""

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Get credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

def check_prospects():
    """Check what's in the prospects table."""
    try:
        response = supabase.table('prospects').select('*').execute()
        
        if response.data:
            print(f"📊 Found {len(response.data)} prospects:")
            print("=" * 50)
            
            for i, prospect in enumerate(response.data, 1):
                print(f"{i}. ID: {prospect.get('id', 'N/A')}")
                print(f"   Brand: {prospect.get('brand_name', 'N/A')}")
                print(f"   Website: {prospect.get('website', 'N/A')}")
                print(f"   Industry: {prospect.get('industry', 'N/A')}")
                print()
        else:
            print("❌ No prospects found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_prospects()
