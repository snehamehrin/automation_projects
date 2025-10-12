#!/usr/bin/env python3
"""
Check the schema of brand_google_reddit table
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


def check_table_schema():
    """Check the schema of brand_google_reddit table."""
    print("🔍 Checking brand_google_reddit table schema")
    print("=" * 50)
    
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found")
        return
    
    # Initialize Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Get one record to see the columns
        response = supabase.table('brand_google_reddit').select('*').limit(1).execute()
        
        if response.data:
            print("✅ Table exists and has data")
            print(f"📊 Columns in brand_google_reddit table:")
            
            # Get the first record to see all columns
            first_record = response.data[0]
            for column, value in first_record.items():
                print(f"   {column}: {type(value).__name__} = {value}")
            
            # Check if processed column exists
            if 'processed' in first_record:
                print(f"\n✅ 'processed' column exists")
                print(f"   Current value: {first_record['processed']}")
            else:
                print(f"\n❌ 'processed' column does NOT exist")
                print(f"   You need to add it with this SQL:")
                print(f"""
    ALTER TABLE brand_google_reddit 
    ADD COLUMN processed BOOLEAN DEFAULT FALSE;
                """)
        else:
            print("❌ Table exists but has no data")
            
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("   The 'brand_google_reddit' table doesn't exist yet.")


if __name__ == "__main__":
    check_table_schema()
