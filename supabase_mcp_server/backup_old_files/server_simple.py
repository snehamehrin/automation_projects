#!/usr/bin/env python3
"""
Simplified MCP Server for Testing
Works without the MCP package for now
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.supabase_mcp.supabase_client import SupabaseClient
from src.supabase_mcp.config import get_settings


class SimpleMCPServer:
    """Simplified MCP server for testing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = SupabaseClient()
        self.tools = {
            "list_tables": self.list_tables,
            "describe_table": self.describe_table,
            "query_table": self.query_table,
            "search_across_tables": self.search_across_tables,
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
                try:
                    response = self.supabase.client.table(table_name).select("*").limit(1).execute()
                    if response.data is not None:
                        found_tables.append(table_name)
                except:
                    pass
            
            if found_tables:
                result = f"# Found {len(found_tables)} tables in your Supabase database:\n\n"
                for table in found_tables:
                    result += f"- **{table}**\n"
                result += "\n**Next steps:**\n"
                result += "- Use `describe_table` to see the structure of any table\n"
                result += "- Use `query_table` to search within specific tables\n"
                return result
            else:
                return "# No common tables found. Your database might have different table names.\n\n**Try:** Use `describe_table` with a specific table name you know exists."
                
        except Exception as e:
            return f"# Error listing tables\n\n**Error:** {str(e)}\n\n**Try:** Check your Supabase connection and credentials."
    
    async def describe_table(self, args: Dict[str, Any]) -> str:
        """Describe table schema"""
        table_name = args.get("table_name", "")
        
        try:
            response = self.supabase.client.table(table_name).select("*").limit(3).execute()
            
            if not response.data:
                return f"# Table: {table_name}\n\n**Status:** Table exists but is empty. Cannot determine schema."
            
            sample_rows = response.data
            columns = list(sample_rows[0].keys())
            
            result = f"# Schema for table: **{table_name}**\n\n"
            result += f"**Columns ({len(columns)}):**\n\n"
            
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
                
                result += f"- **{col}** (`{col_type}`)\n"
                result += f"  Sample: `{sample_value}`\n\n"
            
            result += f"**Sample rows analyzed:** {len(sample_rows)}\n\n"
            result += "**Suggested queries:**\n"
            result += f"- Search text columns: `query_table` with `search_column` and `search_term`\n"
            result += f"- Filter by exact values: `query_table` with `filters`\n"
            
            return result
            
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
            query = self.supabase.client.table(table_name).select("*")
            
            # Text search
            if search_column and search_term:
                query = query.ilike(search_column, f"%{search_term}%")
            
            # Exact match filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            # Limit
            query = query.limit(limit)
            
            response = query.execute()
            results = response.data
            
            result = f"# Query Results from '{table_name}'\n\n"
            result += f"**Found {len(results)} results**\n\n"
            
            if len(results) == 0:
                result += "**No results found** with the given filters.\n\n"
                result += "**Suggestions:**\n"
                result += "- Try different search terms\n"
                result += "- Remove some filters\n"
                result += "- Use `describe_table` to see available columns\n"
                return result
            
            # Display results
            for i, row in enumerate(results, 1):
                result += f"## Result {i}\n\n"
                
                for key, value in row.items():
                    if value is not None:
                        display_value = str(value)
                        if len(display_value) > 300:
                            display_value = display_value[:300] + "..."
                        result += f"**{key}:** {display_value}\n\n"
                
                result += "---\n\n"
            
            if len(results) == limit:
                result += f"**Note:** Showing first {limit} results. Use `limit` parameter to get more.\n\n"
            
            return result
            
        except Exception as e:
            return f"# Error querying table '{table_name}'\n\n**Error:** {str(e)}\n\n**Troubleshooting:**\n- Check table name with `list_tables`\n- Verify column names with `describe_table`"
    
    async def search_across_tables(self, args: Dict[str, Any]) -> str:
        """Search across multiple tables"""
        search_term = args.get("search_term", "")
        tables = args.get("tables", ["reddit_posts", "reddit_comments", "brand_reddit_posts_comments"])
        limit_per_table = args.get("limit_per_table", 10)
        
        result = f"# Search Results for '{search_term}' across tables\n\n"
        result += f"**Searching in:** {', '.join(tables)}\n\n"
        
        total_found = 0
        
        for table_name in tables:
            try:
                # Get a sample to find text columns
                sample = self.supabase.client.table(table_name).select("*").limit(1).execute()
                
                if not sample.data:
                    result += f"## {table_name}: No data found\n\n"
                    continue
                
                # Find text columns
                text_columns = []
                sample_row = sample.data[0]
                
                for key, value in sample_row.items():
                    if isinstance(value, str) and len(value) > 5:
                        text_columns.append(key)
                
                if not text_columns:
                    result += f"## {table_name}: No text columns found\n\n"
                    continue
                
                # Search in each text column
                all_results = []
                for column in text_columns:
                    try:
                        query = self.supabase.client.table(table_name).select("*").ilike(column, f"%{search_term}%").limit(limit_per_table)
                        response = query.execute()
                        all_results.extend(response.data)
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
                    result += f"## Found {len(unique_results)} results in '{table_name}'\n\n"
                    
                    for item in unique_results[:limit_per_table]:
                        for key, value in item.items():
                            if value and isinstance(value, str) and search_term.lower() in value.lower():
                                display_value = str(value)[:400] + "..." if len(str(value)) > 400 else str(value)
                                result += f"**{key}:** {display_value}\n\n"
                        result += "---\n\n"
                else:
                    result += f"## {table_name}: No matches found\n\n"
            
            except Exception as e:
                result += f"## {table_name}: Error - {str(e)}\n\n"
        
        result += f"**Total results found:** {total_found}\n\n"
        return result
    
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
    server = SimpleMCPServer()
    
    print("🚀 Simple MCP Server Started", file=sys.stderr)
    print("📊 Connected to Supabase", file=sys.stderr)
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
