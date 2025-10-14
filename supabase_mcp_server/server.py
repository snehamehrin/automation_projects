"""
Main MCP Server for Supabase
"""

import sys
import anyio
from mcp.server.stdio import stdio_server
from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools


async def main():
    """Main server entry point"""
    try:
        # Create dynamic MCP tools instance
        tools = DynamicSupabaseMCPTools()
        server = tools.get_server()

        # Run the server
        async with stdio_server() as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    anyio.run(main)
