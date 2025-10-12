#!/usr/bin/env python3
"""
Debug script to check what's in your Supabase database.
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


def debug_supabase():
    """Debug what's in your Supabase database."""
    print("🔍 Debugging Supabase Connection")
    print("=" * 50)
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"📡 Supabase URL: {supabase_url}")
    print(f"🔑 Supabase Key: {supabase_key[:20]}..." if supabase_key else "❌ No key")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        return
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Try to read from prospects table
        print("\n📖 Reading from 'prospects' table...")
        try:
            result = supabase.table("prospects").select("*").execute()
            prospects = result.data
            
            print(f"📊 Found {len(prospects)} records in 'prospects' table")
            
            if prospects:
                print("\n📋 Sample records:")
                for i, prospect in enumerate(prospects[:5], 1):
                    print(f"   {i}. {prospect}")
                if len(prospects) > 5:
                    print(f"   ... and {len(prospects) - 5} more records")
            else:
                print("   ❌ No records found in 'prospects' table")
                
        except Exception as e:
            print(f"❌ Error reading from 'prospects' table: {e}")
            
            # Try to list all tables
            print("\n🔍 Trying to list all tables...")
            try:
                # This might not work with all Supabase setups, but worth trying
                result = supabase.rpc('get_tables').execute()
                print(f"📋 Available tables: {result.data}")
            except Exception as e2:
                print(f"❌ Could not list tables: {e2}")
        
        # Try alternative table names
        alternative_tables = ['brands', 'companies', 'leads', 'clients']
        print(f"\n🔍 Checking alternative table names...")
        
        for table_name in alternative_tables:
            try:
                result = supabase.table(table_name).select("*").limit(1).execute()
                if result.data:
                    print(f"✅ Found data in '{table_name}' table: {len(result.data)} records")
                else:
                    print(f"📭 '{table_name}' table exists but is empty")
            except Exception as e:
                print(f"❌ '{table_name}' table doesn't exist or error: {e}")
        
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")


if __name__ == "__main__":
    debug_supabase()
