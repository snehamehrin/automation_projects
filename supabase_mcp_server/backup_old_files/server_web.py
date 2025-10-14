#!/usr/bin/env python3
"""
Web-based MCP Server for Custom Connector
Runs as a web service that Claude Desktop can connect to via URL
"""

import asyncio
import json
import sys
import os
import requests
from typing import Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.supabase_mcp.config import get_settings


class HTTPMCPServer:
    """HTTP-based MCP server for custom connector"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.supabase_url
        self.api_key = self.settings.supabase_key
        self.headers = {
            'apikey': self.api_key,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.tools = {
            "list_tables": self.list_tables,
            "describe_table": self.describe_table,
            "query_table": self.query_table,
            "search_across_tables": self.search_across_tables,
        }
    
    def make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to Supabase"""
        try:
            url = f"{self.base_url}/rest/v1/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            return {
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                'status_code': 500,
                'data': None,
                'error': str(e)
            }
    
    async def list_tables(self, args: Dict[str, Any] = None) -> str:
        """List available tables"""
        try:
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
                result = self.make_request(f"{table_name}?select=*&limit=1")
                if result['status_code'] == 200 and result['data'] is not None:
                    found_tables.append(table_name)
            
            if found_tables:
                response_text = f"# Found {len(found_tables)} tables in your Supabase database:\n\n"
                for table in found_tables:
                    response_text += f"- **{table}**\n"
                response_text += "\n**Next steps:**\n"
                response_text += "- Use `describe_table` to see the structure of any table\n"
                response_text += "- Use `query_table` to search within specific tables\n"
                return response_text
            else:
                return "# No common tables found. Your database might have different table names.\n\n**Try:** Use `describe_table` with a specific table name you know exists."
                
        except Exception as e:
            return f"# Error listing tables\n\n**Error:** {str(e)}\n\n**Try:** Check your Supabase connection and credentials."
    
    async def describe_table(self, args: Dict[str, Any]) -> str:
        """Describe table schema"""
        table_name = args.get("table_name", "")
        
        try:
            result = self.make_request(f"{table_name}?select=*&limit=3")
            
            if result['status_code'] != 200:
                return f"# Error accessing table '{table_name}'\n\n**Error:** {result.get('error', 'Unknown error')}\n\n**Possible causes:**\n- Table doesn't exist\n- Permission denied\n- Network issue"
            
            if not result['data']:
                return f"# Table: {table_name}\n\n**Status:** Table exists but is empty. Cannot determine schema."
            
            sample_rows = result['data']
            columns = list(sample_rows[0].keys())
            
            response_text = f"# Schema for table: **{table_name}**\n\n"
            response_text += f"**Columns ({len(columns)}):**\n\n"
            
            for col in columns:
                values = [row.get(col) for row in sample_rows if row.get(col) is not None]
                col_type = "unknown"
                sample_value = "No data"
                
                if values:
                    sample_value = str(values[0])
                    if len(sample_value) > 100:
                        sample_value = sample_value[:100] + "..."
                    
                    if isinstance(values[0], str):
                        col_type = "text"
                    elif isinstance(values[0], int):
                        col_type = "integer"
                    elif isinstance(values[0], float):
                        col_type = "float"
                    elif isinstance(values[0], bool):
                        col_type = "boolean"
                    else:
                        col_type = type(values[0]).__name__
                
                response_text += f"- **{col}** (`{col_type}`)\n"
                response_text += f"  Sample: `{sample_value}`\n\n"
            
            response_text += f"**Sample rows analyzed:** {len(sample_rows)}\n\n"
            response_text += "**Suggested queries:**\n"
            response_text += f"- Search text columns: `query_table` with `search_column` and `search_term`\n"
            response_text += f"- Filter by exact values: `query_table` with `filters`\n"
            
            return response_text
            
        except Exception as e:
            return f"# Error describing table '{table_name}'\n\n**Error:** {str(e)}\n\n**Possible causes:**\n- Table doesn't exist\n- Permission denied\n- Network issue"
    
    async def query_table(self, args: Dict[str, Any]) -> str:
        """Query table with filters"""
        table_name = args.get("table_name", "")
        search_column = args.get("search_column")
        search_term = args.get("search_term")
        filters = args.get("filters", {})
        limit = args.get("limit", 20)
        
        try:
            params = {'select': '*', 'limit': limit}
            
            if search_column and search_term:
                params[f'{search_column}'] = f'like.*{search_term}*'
            
            for key, value in filters.items():
                params[key] = f'eq.{value}'
            
            result = self.make_request(f"{table_name}", params)
            
            if result['status_code'] != 200:
                return f"# Error querying table '{table_name}'\n\n**Error:** {result.get('error', 'Unknown error')}\n\n**Troubleshooting:**\n- Check table name with `list_tables`\n- Verify column names with `describe_table`"
            
            results = result['data'] or []
            
            response_text = f"# Query Results from '{table_name}'\n\n"
            response_text += f"**Found {len(results)} results**\n\n"
            
            if len(results) == 0:
                response_text += "**No results found** with the given filters.\n\n"
                response_text += "**Suggestions:**\n"
                response_text += "- Try different search terms\n"
                response_text += "- Remove some filters\n"
                response_text += "- Use `describe_table` to see available columns\n"
                return response_text
            
            for i, row in enumerate(results, 1):
                response_text += f"## Result {i}\n\n"
                
                for key, value in row.items():
                    if value is not None:
                        display_value = str(value)
                        if len(display_value) > 300:
                            display_value = display_value[:300] + "..."
                        response_text += f"**{key}:** {display_value}\n\n"
                
                response_text += "---\n\n"
            
            if len(results) == limit:
                response_text += f"**Note:** Showing first {limit} results. Use `limit` parameter to get more.\n\n"
            
            return response_text
            
        except Exception as e:
            return f"# Error querying table '{table_name}'\n\n**Error:** {str(e)}\n\n**Troubleshooting:**\n- Check table name with `list_tables`\n- Verify column names with `describe_table`"
    
    async def search_across_tables(self, args: Dict[str, Any]) -> str:
        """Search across multiple tables"""
        search_term = args.get("search_term", "")
        tables = args.get("tables", ["reddit_posts", "reddit_comments", "brand_reddit_posts_comments"])
        limit_per_table = args.get("limit_per_table", 10)
        
        response_text = f"# Search Results for '{search_term}' across tables\n\n"
        response_text += f"**Searching in:** {', '.join(tables)}\n\n"
        
        total_found = 0
        
        for table_name in tables:
            try:
                sample_result = self.make_request(f"{table_name}?select=*&limit=1")
                
                if sample_result['status_code'] != 200 or not sample_result['data']:
                    response_text += f"## {table_name}: No data found\n\n"
                    continue
                
                text_columns = []
                sample_row = sample_result['data'][0]
                
                for key, value in sample_row.items():
                    if isinstance(value, str) and len(value) > 5:
                        text_columns.append(key)
                
                if not text_columns:
                    response_text += f"## {table_name}: No text columns found\n\n"
                    continue
                
                all_results = []
                for column in text_columns:
                    try:
                        params = {
                            'select': '*',
                            'limit': limit_per_table,
                            column: f'like.*{search_term}*'
                        }
                        result = self.make_request(f"{table_name}", params)
                        if result['status_code'] == 200 and result['data']:
                            all_results.extend(result['data'])
                    except:
                        continue
                
                seen = set()
                unique_results = []
                for item in all_results:
                    item_id = item.get('id') or str(item)
                    if item_id not in seen:
                        seen.add(item_id)
                        unique_results.append(item)
                
                if unique_results:
                    total_found += len(unique_results)
                    response_text += f"## Found {len(unique_results)} results in '{table_name}'\n\n"
                    
                    for item in unique_results[:limit_per_table]:
                        for key, value in item.items():
                            if value and isinstance(value, str) and search_term.lower() in value.lower():
                                display_value = str(value)[:400] + "..." if len(str(value)) > 400 else str(value)
                                response_text += f"**{key}:** {display_value}\n\n"
                        response_text += "---\n\n"
                else:
                    response_text += f"## {table_name}: No matches found\n\n"
            
            except Exception as e:
                response_text += f"## {table_name}: Error - {str(e)}\n\n"
        
        response_text += f"**Total results found:** {total_found}\n\n"
        return response_text
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "list_tables",
                        "description": "List all tables available in the Supabase database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "describe_table",
                        "description": "Get the schema/structure of a specific table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table_name": {
                                    "type": "string",
                                    "description": "Name of the table to describe"
                                }
                            },
                            "required": ["table_name"]
                        }
                    },
                    {
                        "name": "query_table",
                        "description": "Query any table with flexible filters",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string"},
                                "search_column": {"type": "string"},
                                "search_term": {"type": "string"},
                                "filters": {"type": "object"},
                                "limit": {"type": "integer", "default": 20}
                            },
                            "required": ["table_name"]
                        }
                    },
                    {
                        "name": "search_across_tables",
                        "description": "Search for a term across multiple tables",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "search_term": {"type": "string"},
                                "tables": {"type": "array", "items": {"type": "string"}},
                                "limit_per_table": {"type": "integer", "default": 10}
                            },
                            "required": ["search_term"]
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name](arguments)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                except Exception as e:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error executing {tool_name}: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {tool_name}"
                        }
                    ],
                    "isError": True
                }
        
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown method: {method}"
                    }
                ],
                "isError": True
            }


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server"""
    
    def __init__(self, mcp_server, *args, **kwargs):
        self.mcp_server = mcp_server
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/mcp':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data.decode('utf-8'))
                response = asyncio.run(self.mcp_server.handle_request(request))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {
                    "content": [{"type": "text", "text": f"Server error: {str(e)}"}],
                    "isError": True
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Supabase MCP Server</title>
            </head>
            <body>
                <h1>🚀 Supabase MCP Server</h1>
                <p>Server is running and ready to accept MCP requests.</p>
                <p>Endpoint: <code>POST /mcp</code></p>
                <p>Available tools:</p>
                <ul>
                    <li>list_tables</li>
                    <li>describe_table</li>
                    <li>query_table</li>
                    <li>search_across_tables</li>
                </ul>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def create_handler(mcp_server):
    """Create request handler with MCP server"""
    def handler(*args, **kwargs):
        return MCPRequestHandler(mcp_server, *args, **kwargs)
    return handler


def main():
    """Main server function"""
    mcp_server = HTTPMCPServer()
    
    port = 8080
    server_address = ('localhost', port)
    
    handler = create_handler(mcp_server)
    httpd = HTTPServer(server_address, handler)
    
    print(f"🚀 Supabase MCP Server started on http://localhost:{port}")
    print("📊 Connected to Supabase via HTTP")
    print("🔧 Available tools: list_tables, describe_table, query_table, search_across_tables")
    print(f"🌐 Web interface: http://localhost:{port}")
    print(f"🔗 MCP endpoint: http://localhost:{port}/mcp")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()


if __name__ == "__main__":
    main()
