#!/usr/bin/env python3
"""
HTTP-based MCP Server for Testing
Uses HTTP requests instead of Supabase client to avoid compatibility issues
"""

import asyncio
import json
import sys
import os
import requests
from typing import Dict, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.supabase_mcp.config import get_settings


class HTTPMCPServer:
    """HTTP-based MCP server for testing"""
    
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
            # Try common table names
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
            # Build query parameters
            params = {'select': '*', 'limit': limit}
            
            # Add text search
            if search_column and search_term:
                params[f'{search_column}'] = f'like.*{search_term}*'
            
            # Add exact match filters
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
            
            # Display results
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
                # Get a sample to find text columns
                sample_result = self.make_request(f"{table_name}?select=*&limit=1")
                
                if sample_result['status_code'] != 200 or not sample_result['data']:
                    response_text += f"## {table_name}: No data found\n\n"
                    continue
                
                # Find text columns
                text_columns = []
                sample_row = sample_result['data'][0]
                
                for key, value in sample_row.items():
                    if isinstance(value, str) and len(value) > 5:
                        text_columns.append(key)
                
                if not text_columns:
                    response_text += f"## {table_name}: No text columns found\n\n"
                    continue
                
                # Search in each text column
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
                
                # Remove duplicates
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


async def main():
    """Main server loop"""
    server = HTTPMCPServer()
    
    print("🚀 HTTP-based MCP Server Started", file=sys.stderr)
    print("📊 Connected to Supabase via HTTP", file=sys.stderr)
    print("🔧 Available tools: list_tables, describe_table, query_table, search_across_tables", file=sys.stderr)
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Server error: {str(e)}"
                        }
                    ],
                    "isError": True
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("🛑 Server stopped", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
