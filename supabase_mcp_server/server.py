"""
Main MCP Server for Supabase
"""

import asyncio
import sys
from mcp.server.stdio import stdio_server
from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools


async def main():
    """Main server entry point"""
    # Create dynamic MCP tools instance
    tools = DynamicSupabaseMCPTools()
    server = tools.get_server()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
