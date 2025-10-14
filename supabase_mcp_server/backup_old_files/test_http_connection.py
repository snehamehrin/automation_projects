#!/usr/bin/env python3
"""
HTTP Connection Test to Supabase
Tests if Supabase project is accessible via HTTP
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_http_connection():
    """Test HTTP connection to Supabase"""
    
    print("🚀 HTTP Supabase Connection Test")
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
    
    # Test HTTP connection
    try:
        # Test the REST API endpoint
        api_url = f"{url}/rest/v1/"
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        print("🔍 Testing HTTP connection to Supabase...")
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ HTTP connection successful!")
            print("✅ Supabase project is accessible")
            
            # Try to get table information
            try:
                tables_url = f"{url}/rest/v1/reddit_posts?select=*&limit=1"
                tables_response = requests.get(tables_url, headers=headers, timeout=10)
                
                if tables_response.status_code == 200:
                    data = tables_response.json()
                    print("✅ Successfully queried reddit_posts table")
                    print(f"✅ Retrieved {len(data)} row(s)")
                    return True
                elif tables_response.status_code == 404:
                    print("⚠️  Table 'reddit_posts' doesn't exist")
                    print("💡 This is normal - your database might have different table names")
                    print("✅ Connection to Supabase is working!")
                    return True
                else:
                    print(f"⚠️  Table query returned status: {tables_response.status_code}")
                    print("✅ But HTTP connection is working!")
                    return True
                    
            except Exception as e:
                print(f"⚠️  Table query error: {e}")
                print("✅ But HTTP connection is working!")
                return True
                
        else:
            print(f"❌ HTTP connection failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_http_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 HTTP connection test successful!")
        print("\nYour Supabase project is accessible!")
        print("The MCP server foundation is solid.")
        print("\nNext steps:")
        print("1. Wait for MCP package compatibility fix")
        print("2. Or use the HTTP-based approach for now")
        print("3. Connect to Claude Desktop when ready")
    else:
        print("❌ HTTP connection test failed")
        print("Check your Supabase credentials and project status")
    
    exit(0 if success else 1)
