#!/usr/bin/env python3
"""
Read-only test for Supabase connection.

This script only tests reading from your prospects table - no writing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client


async def test_read_prospects():
    """Test reading prospects from Supabase."""
    print("🔗 Testing Supabase Connection (Read-Only)")
    print("=" * 45)
    
    try:
        # Get Supabase credentials from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials!")
            print("Please check your .env file has:")
            print("- SUPABASE_URL")
            print("- SUPABASE_KEY")
            return False
        
        print(f"📡 Connecting to: {supabase_url}")
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by reading from prospects table
        print("📖 Reading prospects from database...")
        
        try:
            result = supabase.table("prospects").select("*").execute()
            prospects = result.data
            
            print(f"📊 Found {len(prospects)} prospects in database:")
            
            if prospects:
                for i, prospect in enumerate(prospects, 1):
                    print(f"   {i}. {prospect.get('name', 'Unknown')}")
                    if prospect.get('category'):
                        print(f"      Category: {prospect['category']}")
                    if prospect.get('company_url'):
                        print(f"      URL: {prospect['company_url']}")
                    print()
            else:
                print("   No prospects found in the database")
                print("   The 'prospects' table exists but is empty")
            
            print("✅ Connection successful!")
            print("✅ Can read from prospects table!")
            return True
            
        except Exception as e:
            print(f"❌ Error reading prospects: {e}")
            
            # Check if table exists
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                print("   The 'prospects' table doesn't exist yet.")
                print("   Please create it in your Supabase dashboard → SQL Editor:")
                print("""
                CREATE TABLE prospects (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    company_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """)
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Supabase Read-Only Test")
    print("=" * 50)
    
    # Test reading prospects
    success = await test_read_prospects()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Read test successful!")
        print("\nYour Supabase connection is working correctly.")
        print("You can now:")
        print("1. See what prospects are in your database")
        print("2. Run analysis on those prospects")
        print("3. Use the API to read prospect data")
    else:
        print("❌ Read test failed!")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct SUPABASE_URL and SUPABASE_KEY")
        print("2. Verify your Supabase project is active")
        print("3. Make sure the 'prospects' table exists in your database")
        print("4. Install HTTP2 support: pip install 'httpx[http2]'")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
