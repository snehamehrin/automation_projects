#!/usr/bin/env python3
"""
Quick Test Script for Dynamic Supabase MCP Server
Tests basic functionality without requiring database connection
"""

import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock


async def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
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
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        print("✅ MCP tools imported")
    except Exception as e:
        print(f"❌ MCP tools import failed: {e}")
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
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_mcp_tools_creation():
    """Test MCP tools creation with mocked dependencies"""
    print("\n🧪 Testing MCP tools creation...")
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        
        # Mock the SupabaseClient
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            mock_client.return_value = Mock()
            
            tools = DynamicSupabaseMCPTools()
            server = tools.get_server()
            
            print("✅ MCP tools created successfully")
            print(f"✅ Server name: {server.name}")
            return True
    except Exception as e:
        print(f"❌ MCP tools creation failed: {e}")
        return False


async def test_tool_registration():
    """Test that tools are properly registered"""
    print("\n🧪 Testing tool registration...")
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            mock_client.return_value = Mock()
            
            tools = DynamicSupabaseMCPTools()
            
            # Check that tools are registered
            expected_tools = [
                "list_tables",
                "describe_table", 
                "query_table",
                "search_across_tables",
                "insert_data",
                "update_data",
                "delete_data"
            ]
            
            # This is a bit tricky to test without running the actual server
            # But we can verify the class has the expected methods
            for tool_name in expected_tools:
                method_name = f"_list_tables_impl" if tool_name == "list_tables" else f"_{tool_name}_impl"
                if hasattr(tools, method_name):
                    print(f"✅ Tool '{tool_name}' method found")
                else:
                    print(f"❌ Tool '{tool_name}' method missing")
                    return False
            
            print("✅ All tools properly registered")
            return True
    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        return False


async def test_mock_operations():
    """Test tool operations with mocked data"""
    print("\n🧪 Testing mock operations...")
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            # Create mock client with realistic responses
            mock_client_instance = Mock()
            mock_client_instance.client = Mock()
            mock_client_instance.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
                {"id": 1, "title": "Test post", "body": "Test content", "score": 10}
            ]
            mock_client.return_value = mock_client_instance
            
            tools = DynamicSupabaseMCPTools()
            
            # Test describe_table with mock data
            result = await tools._describe_table_impl({"table_name": "test_table"})
            
            if result and len(result) > 0:
                print("✅ Mock describe_table operation successful")
                print(f"✅ Response length: {len(result[0].text)} characters")
            else:
                print("❌ Mock describe_table operation failed")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Mock operations test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling"""
    print("\n🧪 Testing error handling...")
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            # Create mock client that raises exceptions
            mock_client_instance = Mock()
            mock_client_instance.client = Mock()
            mock_client_instance.client.table.side_effect = Exception("Connection failed")
            mock_client.return_value = mock_client_instance
            
            tools = DynamicSupabaseMCPTools()
            
            # Test error handling
            result = await tools._describe_table_impl({"table_name": "nonexistent_table"})
            
            if result and len(result) > 0 and "Error" in result[0].text:
                print("✅ Error handling working correctly")
                print(f"✅ Error message: {result[0].text[:100]}...")
            else:
                print("❌ Error handling failed")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all quick tests"""
    print("🚀 Dynamic Supabase MCP Server - Quick Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_mcp_tools_creation,
        test_tool_registration,
        test_mock_operations,
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
        print("🎉 All tests passed! The MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Set up your .env file with Supabase credentials")
        print("2. Run: python examples/dynamic_discovery_demo.py")
        print("3. Test with real database: python examples/basic_usage.py")
        print("4. Connect to Claude Desktop for full testing")
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
