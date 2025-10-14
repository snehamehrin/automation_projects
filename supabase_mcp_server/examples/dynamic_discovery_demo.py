"""
Dynamic Discovery Demo
Shows how the intelligent MCP server works
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Note: This demo requires the MCP package to be installed
# For now, we'll use a simplified version that doesn't require MCP
try:
    from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️  MCP package not available. Using simplified demo.")
    MCP_AVAILABLE = False


async def demo_dynamic_discovery():
    """Demonstrate the dynamic discovery capabilities"""
    
    print("🚀 Dynamic Supabase MCP Server Demo")
    print("=" * 50)
    
    if not MCP_AVAILABLE:
        print("❌ MCP package not available. Please install with: pip install mcp")
        print("   For now, run: python examples/simple_demo.py")
        return
    
    # Initialize the tools
    tools = DynamicSupabaseMCPTools()
    
    # Demo 1: List tables (discovery)
    print("\n1️⃣ Discovering available tables...")
    try:
        result = await tools._list_tables_impl()
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")
    
    # Demo 2: Describe a table (schema analysis)
    print("\n2️⃣ Analyzing table schema...")
    try:
        result = await tools._describe_table_impl({"table_name": "reddit_posts"})
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")
    
    # Demo 3: Smart search across tables
    print("\n3️⃣ Searching across multiple tables...")
    try:
        result = await tools._search_across_tables_impl({
            "search_term": "Knix",
            "tables": ["reddit_posts", "reddit_comments", "brand_reddit_posts_comments"],
            "limit_per_table": 5
        })
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")
    
    # Demo 4: Flexible querying
    print("\n4️⃣ Flexible table querying...")
    try:
        result = await tools._query_table_impl({
            "table_name": "reddit_posts",
            "search_column": "title",
            "search_term": "review",
            "min_score": 5,
            "order_by": "score",
            "limit": 10
        })
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ Demo complete!")
    print("\n💡 Key Features Demonstrated:")
    print("- Intelligent table discovery")
    print("- Schema analysis and type detection")
    print("- Cross-table search capabilities")
    print("- Flexible querying with multiple filters")
    print("- Smart result formatting and suggestions")


if __name__ == "__main__":
    asyncio.run(demo_dynamic_discovery())
