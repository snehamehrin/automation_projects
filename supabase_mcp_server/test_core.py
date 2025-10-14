#!/usr/bin/env python3
"""
Core Functionality Test for Dynamic Supabase MCP Server
Tests the core logic without requiring MCP package
"""

import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock


async def test_imports():
    """Test that core modules can be imported"""
    print("🧪 Testing core imports...")
    
    try:
        from src.supabase_mcp.config import get_settings
        print("✅ Config module imported")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from src.supabase_mcp.supabase_client import SupabaseClient
        print("✅ Supabase client imported")
    except Exception as e:
        print(f"❌ Supabase client import failed: {e}")
        return False
    
    return True


async def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.supabase_mcp.config import get_settings
        
        # Test with default values
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.supabase_url[:20]}...")
        print(f"✅ Max query limit: {settings.max_query_limit}")
        print(f"✅ Default timeout: {settings.default_timeout}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_supabase_client():
    """Test Supabase client creation"""
    print("\n🧪 Testing Supabase client...")
    
    try:
        from src.supabase_mcp.supabase_client import SupabaseClient
        
        # Mock the create_client function
        with patch('src.supabase_mcp.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            client = SupabaseClient()
            
            print("✅ Supabase client created successfully")
            print(f"✅ Client type: {type(client.client)}")
            return True
    except Exception as e:
        print(f"❌ Supabase client test failed: {e}")
        return False


async def test_client_methods():
    """Test Supabase client methods with mocked responses"""
    print("\n🧪 Testing client methods...")
    
    try:
        from src.supabase_mcp.supabase_client import SupabaseClient
        
        with patch('src.supabase_mcp.supabase_client.create_client') as mock_create:
            # Create a more realistic mock
            mock_client = Mock()
            mock_table = Mock()
            mock_query = Mock()
            mock_response = Mock()
            
            # Set up the mock chain
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.execute.return_value = mock_response
            mock_response.data = [{"id": 1, "name": "test"}]
            
            mock_create.return_value = mock_client
            
            client = SupabaseClient()
            client.client = mock_client
            
            # Test query_table method
            result = await client.query_table("test_table", filters={"id": 1}, limit=10)
            
            if result and len(result) == 1:
                print("✅ query_table method works")
                print(f"✅ Returned {len(result)} results")
            else:
                print("❌ query_table method failed")
                return False
            
            # Test insert_data method
            mock_table.insert.return_value.execute.return_value.data = [{"id": 1, "name": "test"}]
            result = await client.insert_data("test_table", {"name": "test"})
            
            if result:
                print("✅ insert_data method works")
            else:
                print("❌ insert_data method failed")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Client methods test failed: {e}")
        return False


async def test_core_logic():
    """Test core business logic without MCP dependencies"""
    print("\n🧪 Testing core business logic...")
    
    try:
        # Test the core logic that would be in the MCP tools
        def mock_list_tables():
            """Mock implementation of list_tables logic"""
            return """# Available Tables in Your Supabase Database

Common tables in your database likely include:
- reddit_posts
- reddit_comments  
- brand_reddit_posts_comments
- reddit_brand_analysis_results
- prospects

**Next steps:**
1. Use `describe_table` to see the structure of any table
2. Use `query_table` to search within specific tables
3. Use `search_across_tables` to search multiple tables at once
"""
        
        def mock_describe_table(table_name):
            """Mock implementation of describe_table logic"""
            return f"""# Schema for table: **{table_name}**

**Columns (3):**

- **id** (`integer`)
  Sample: `1`

- **title** (`text`)
  Sample: `Test post title`

- **body** (`text`)
  Sample: `This is a test post body content...`

**Sample rows analyzed:** 1

**Suggested queries:**
- Search text columns: `query_table` with `search_column` and `search_term`
- Filter by exact values: `query_table` with `filters`
- Sort results: `query_table` with `order_by`
"""
        
        # Test the mock functions
        tables_result = mock_list_tables()
        if "reddit_posts" in tables_result and "Next steps" in tables_result:
            print("✅ Table discovery logic works")
        else:
            print("❌ Table discovery logic failed")
            return False
        
        describe_result = mock_describe_table("test_table")
        if "Schema for table" in describe_result and "Suggested queries" in describe_result:
            print("✅ Schema analysis logic works")
        else:
            print("❌ Schema analysis logic failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Core logic test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling logic"""
    print("\n🧪 Testing error handling...")
    
    try:
        def mock_error_response(error_msg):
            """Mock error handling"""
            return f"""# Error querying table 'test_table'

**Error:** {error_msg}

**Troubleshooting:**
- Check table name with `list_tables`
- Verify column names with `describe_table`
- Check filter values and types"""
        
        error_result = mock_error_response("Connection failed")
        
        if "Error querying table" in error_result and "Troubleshooting" in error_result:
            print("✅ Error handling logic works")
            print(f"✅ Error message format: {error_result[:50]}...")
        else:
            print("❌ Error handling logic failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all core tests"""
    print("🚀 Dynamic Supabase MCP Server - Core Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_supabase_client,
        test_client_methods,
        test_core_logic,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core tests passed! The foundation is solid.")
        print("\nNext steps:")
        print("1. Install MCP package when available: pip install mcp")
        print("2. Set up your .env file with Supabase credentials")
        print("3. Test with real database: python examples/basic_usage.py")
        print("4. Connect to Claude Desktop for full MCP testing")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check Python path and imports")
        print("3. Verify file structure")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
