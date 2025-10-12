#!/usr/bin/env python3
"""
Simple test to check Supabase connection and read brands.

Run this script to test your Supabase setup:
python simple_test.py
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


async def test_supabase_connection():
    """Test Supabase connection and read brands."""
    print("🔗 Testing Supabase Connection")
    print("=" * 40)
    
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
        
        # Test connection by trying to read from prospects table
        print("📖 Reading prospects from database...")
        
        try:
            result = supabase.table("prospects").select("*").execute()
            brands = result.data
            
            print(f"📊 Found {len(brands)} prospects in database:")
            
            if brands:
                for i, prospect in enumerate(brands, 1):
                    print(f"   {i}. {prospect.get('name', 'Unknown')}")
                    if prospect.get('category'):
                        print(f"      Category: {prospect['category']}")
                    if prospect.get('company_url'):
                        print(f"      URL: {prospect['company_url']}")
                    print()
            else:
                print("   No prospects found in the database")
                print("   You may need to add some prospects to the 'prospects' table")
            
            print("✅ Connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ Error reading brands: {e}")
            
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


async def test_add_brand():
    """Test adding a brand to the database."""
    print("\n📝 Testing brand insertion...")
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Try to add a test brand
        test_brand = {
            'name': 'Test Brand',
            'category': 'Test Category',
            'company_url': 'https://test.com'
        }
        
        result = supabase.table("prospects").insert(test_brand).execute()
        
        if result.data:
            print(f"✅ Successfully added test brand: {result.data[0].get('id', 'N/A')}")
            return True
        else:
            print("❌ Failed to add test brand")
            return False
            
    except Exception as e:
        print(f"❌ Error adding brand: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Supabase Connection Test")
    print("=" * 50)
    
    # Test connection and reading
    connection_ok = await test_supabase_connection()
    
    if connection_ok:
        # Test writing
        write_ok = await test_add_brand()
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"   Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
        print(f"   Reading: {'✅ PASS' if connection_ok else '❌ FAIL'}")
        print(f"   Writing: {'✅ PASS' if write_ok else '❌ FAIL'}")
        
        if connection_ok and write_ok:
            print("\n🎉 All tests passed! Your Supabase setup is working correctly.")
            print("\nNext steps:")
            print("1. Add some real brands to your 'brands' table")
            print("2. Run: python test_analysis.py")
        elif connection_ok:
            print("\n✅ Connection works, but writing failed.")
            print("This might be expected if you have read-only permissions.")
        else:
            print("\n❌ Connection failed. Please check your credentials.")
    else:
        print("\n❌ Connection test failed!")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct SUPABASE_URL and SUPABASE_KEY")
        print("2. Verify your Supabase project is active")
        print("3. Make sure the 'brands' table exists in your database")
    
    return connection_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)