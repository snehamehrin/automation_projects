#!/usr/bin/env python3
"""
Simple Supabase Connection Test
Tests connection without the proxy argument issue
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_connection():
    """Test simple Supabase connection"""
    
    print("🚀 Simple Supabase Connection Test")
    print("=" * 40)
    
    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    print(f"✅ URL: {url[:30]}...")
    print(f"✅ Key: {key[:20]}...")
    
    if not url or not key:
        print("❌ Missing credentials")
        return False
    
    if "your_supabase_url_here" in url:
        print("❌ Still using placeholder URL")
        return False
    
    # Try to create client with minimal options
    try:
        from supabase import create_client
        
        # Create client without proxy options
        client = create_client(url, key)
        print("✅ Supabase client created successfully")
        
        # Try a simple query to test connection
        try:
            # Try to query a common table
            response = client.table('reddit_posts').select('*').limit(1).execute()
            print("✅ Successfully connected to database!")
            print(f"✅ Found table: reddit_posts")
            
            if response.data:
                print(f"✅ Retrieved {len(response.data)} row(s)")
                print("✅ Database connection is working!")
                return True
            else:
                print("⚠️  Table exists but is empty")
                return True
                
        except Exception as e:
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                print("⚠️  Table 'reddit_posts' doesn't exist")
                print("💡 This is normal - your database might have different table names")
                print("✅ Connection to Supabase is working!")
                return True
            else:
                print(f"❌ Query error: {error_msg}")
                return False
                
    except Exception as e:
        print(f"❌ Client creation error: {e}")
        return False


if __name__ == "__main__":
    success = test_simple_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Connection test successful!")
        print("\nYour MCP server is ready!")
        print("Next steps:")
        print("1. Wait for MCP package to become available")
        print("2. Connect to Claude Desktop")
        print("3. Start querying your database with natural language")
    else:
        print("❌ Connection test failed")
        print("Check your Supabase credentials and project status")
    
    exit(0 if success else 1)
