"""
MCP Server for Supabase - Remote HTTP/SSE Version
Runs on a VPS and connects via HTTP
"""

import sys
import os
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response
from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools


# Initialize MCP tools and server
tools = DynamicSupabaseMCPTools()
server = tools.get_server()

# Create SSE transport
sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    """Handle SSE connections"""
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send  # type: ignore
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options()
        )
    return Response()


async def health_check(request: Request):
    """Health check endpoint"""
    return Response(content="OK", status_code=200)


# Create Starlette app
app = Starlette(
    debug=False,
    routes=[
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Starting Supabase MCP Server on {host}:{port}", file=sys.stderr)
    print(f"📡 SSE endpoint: http://{host}:{port}/sse", file=sys.stderr)
    print(f"💓 Health check: http://{host}:{port}/health", file=sys.stderr)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
