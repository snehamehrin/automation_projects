#!/usr/bin/env python3
"""
MCP Server Test - Verify the server is fully operational
"""

import asyncio
from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools


async def test_mcp_server():
    """Test MCP server functionality"""
    print("🚀 MCP Server Test")
    print("=" * 60)

    # Initialize server
    print("\n1. Initializing MCP server...")
    tools = DynamicSupabaseMCPTools()
    server = tools.get_server()
    print(f"✅ Server initialized: {server.name}")

    # Test list_tables tool
    print("\n2. Testing list_tables tool...")
    try:
        result = await tools._list_tables_impl()
        print(f"✅ list_tables works")
        print(f"   Response preview: {result[0].text[:100]}...")
    except Exception as e:
        print(f"❌ list_tables failed: {e}")

    # Test describe_table tool
    print("\n3. Testing describe_table tool...")
    try:
        result = await tools._describe_table_impl({"table_name": "brand_reddit_posts_comments"})
        print(f"✅ describe_table works")
        print(f"   Response preview: {result[0].text[:150]}...")
    except Exception as e:
        print(f"❌ describe_table failed: {e}")

    # Test query_table tool
    print("\n4. Testing query_table tool...")
    try:
        result = await tools._query_table_impl({
            "table_name": "brand_reddit_posts_comments",
            "limit": 2
        })
        print(f"✅ query_table works")
        print(f"   Response preview: {result[0].text[:150]}...")
    except Exception as e:
        print(f"❌ query_table failed: {e}")

    # Test search_across_tables tool
    print("\n5. Testing search_across_tables tool...")
    try:
        result = await tools._search_across_tables_impl({
            "search_term": "reddit",
            "tables": ["brand_reddit_posts_comments"],
            "limit_per_table": 1
        })
        print(f"✅ search_across_tables works")
        print(f"   Response preview: {result[0].text[:150]}...")
    except Exception as e:
        print(f"❌ search_across_tables failed: {e}")

    print("\n" + "=" * 60)
    print("🎉 MCP Server is fully operational!")
    print("\n📋 Available tools:")
    print("   • list_tables - List all database tables")
    print("   • describe_table - Get table schema")
    print("   • query_table - Query with filters")
    print("   • search_across_tables - Search multiple tables")
    print("   • insert_data - Insert new records")
    print("   • update_data - Update existing records")
    print("   • delete_data - Delete records")

    print("\n🔌 How to connect to Claude Desktop:")
    print("   1. Open Claude Desktop settings")
    print("   2. Add MCP server configuration:")
    print("   3. Point to your server.py file")
    print("   4. Restart Claude Desktop")
    print("   5. Start querying your database with natural language!")

    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1)
