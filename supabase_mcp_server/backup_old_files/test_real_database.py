#!/usr/bin/env python3
"""
Test Real Database Connection
Tests the MCP server with actual Supabase database
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.supabase_mcp.supabase_client import SupabaseClient
from src.supabase_mcp.config import get_settings


async def test_real_database():
    """Test with real Supabase database"""
    
    print("🚀 Testing Real Supabase Database Connection")
    print("=" * 50)
    
    # Test 1: Configuration
    print("\n1️⃣ Configuration Test")
    try:
        settings = get_settings()
        print(f"✅ Supabase URL: {settings.supabase_url[:30]}...")
        print(f"✅ Max query limit: {settings.max_query_limit}")
        
        if "your_supabase_url_here" in settings.supabase_url:
            print("⚠️  Using placeholder URL - please update .env file")
            return False
        else:
            print("✅ Real Supabase URL detected")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test 2: Real Database Connection
    print("\n2️⃣ Real Database Connection Test")
    try:
        client = SupabaseClient()
        print("✅ Supabase client created")
        
        # Try to list tables by attempting a simple query
        # This will fail gracefully if tables don't exist
        print("🔍 Attempting to discover tables...")
        
        # Try common table names
        common_tables = [
            "reddit_posts",
            "reddit_comments", 
            "brand_reddit_posts_comments",
            "reddit_brand_analysis_results",
            "prospects",
            "google_results"
        ]
        
        found_tables = []
        for table_name in common_tables:
            try:
                # Try to query the table (limit 1 to avoid large responses)
                response = client.client.table(table_name).select("*").limit(1).execute()
                if response.data is not None:
                    found_tables.append(table_name)
                    print(f"✅ Found table: {table_name}")
            except Exception as e:
                print(f"❌ Table {table_name} not found or error: {str(e)[:50]}...")
        
        if found_tables:
            print(f"\n🎉 Successfully connected! Found {len(found_tables)} tables:")
            for table in found_tables:
                print(f"   - {table}")
            
            # Test 3: Query Real Data
            print(f"\n3️⃣ Query Real Data from {found_tables[0]}")
            try:
                # Get a few rows from the first found table
                response = client.client.table(found_tables[0]).select("*").limit(3).execute()
                
                if response.data:
                    print(f"✅ Retrieved {len(response.data)} rows from {found_tables[0]}")
                    
                    # Show sample data
                    for i, row in enumerate(response.data, 1):
                        print(f"\n   Row {i}:")
                        for key, value in row.items():
                            if value is not None:
                                display_value = str(value)
                                if len(display_value) > 100:
                                    display_value = display_value[:100] + "..."
                                print(f"     {key}: {display_value}")
                else:
                    print(f"⚠️  Table {found_tables[0]} exists but is empty")
                    
            except Exception as e:
                print(f"❌ Error querying {found_tables[0]}: {e}")
            
            return True
        else:
            print("❌ No common tables found. Your database might have different table names.")
            print("💡 Try creating a table or check your table names in Supabase dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your SUPABASE_URL in .env file")
        print("2. Check your SUPABASE_KEY in .env file")
        print("3. Verify your Supabase project is active")
        print("4. Check your Row Level Security (RLS) policies")
        return False


async def main():
    """Main test function"""
    success = await test_real_database()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Real database connection successful!")
        print("\nNext steps:")
        print("1. Your MCP server is ready for Claude Desktop integration")
        print("2. Once MCP package is available, you can connect to Claude")
        print("3. You can query your database using natural language")
    else:
        print("⚠️  Database connection failed")
        print("\nTroubleshooting:")
        print("1. Update your .env file with correct Supabase credentials")
        print("2. Check your Supabase project status")
        print("3. Verify your database has data")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
