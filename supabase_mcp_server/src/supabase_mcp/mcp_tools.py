"""
Dynamic Discovery MCP Tools for Supabase
Intelligent table discovery and flexible querying
"""

from typing import Dict, List, Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from .supabase_client import SupabaseClient


class DynamicSupabaseMCPTools:
    """Dynamic MCP tools for Supabase database operations with intelligent discovery"""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.server = Server("supabase-intelligence")
        self._register_tools()
    
    def _register_tools(self):
        """Register all dynamic MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available dynamic Supabase tools"""
            return [
                Tool(
                    name="list_tables",
                    description="List all tables available in the Supabase database. Use this first to discover what data is available.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="describe_table",
                    description="Get the schema/structure of a specific table (column names and types). Use this to understand what data you can query.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to describe"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="query_table",
                    description="Query any table with flexible filters. Can search by text, filter by values, limit results, and order by columns.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to query"
                            },
                            "search_column": {
                                "type": "string",
                                "description": "Column to search in (optional, for text search)"
                            },
                            "search_term": {
                                "type": "string",
                                "description": "Term to search for (optional, uses case-insensitive LIKE)"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Exact match filters (optional). Example: {'subreddit': 'ABraThatFits', 'score': 10}",
                                "additionalProperties": True
                            },
                            "min_score": {
                                "type": "integer",
                                "description": "Minimum score/upvotes (optional)"
                            },
                            "order_by": {
                                "type": "string",
                                "description": "Column to sort by (optional)"
                            },
                            "order_desc": {
                                "type": "boolean",
                                "description": "Sort descending? (default: true)",
                                "default": True
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 20)",
                                "default": 20
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="search_across_tables",
                    description="Search for a term across multiple tables at once. Useful when you're not sure which table contains the data.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Term to search for across all tables"
                            },
                            "tables": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of table names to search (optional, defaults to common tables)"
                            },
                            "limit_per_table": {
                                "type": "integer",
                                "description": "Max results per table (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="insert_data",
                    description="Insert data into a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to insert into"
                            },
                            "data": {
                                "type": "object",
                                "description": "Data to insert",
                                "additionalProperties": True
                            }
                        },
                        "required": ["table_name", "data"]
                    }
                ),
                Tool(
                    name="update_data",
                    description="Update data in a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to update"
                            },
                            "data": {
                                "type": "object",
                                "description": "Data to update",
                                "additionalProperties": True
                            },
                            "filters": {
                                "type": "object",
                                "description": "Key-value pairs for filtering which rows to update",
                                "additionalProperties": True
                            }
                        },
                        "required": ["table_name", "data", "filters"]
                    }
                ),
                Tool(
                    name="delete_data",
                    description="Delete data from a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to delete from"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Key-value pairs for filtering which rows to delete",
                                "additionalProperties": True
                            }
                        },
                        "required": ["table_name", "filters"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Route tool calls to appropriate handlers"""
            
            if name == "list_tables":
                return await self._list_tables_impl()
            elif name == "describe_table":
                return await self._describe_table_impl(arguments)
            elif name == "query_table":
                return await self._query_table_impl(arguments)
            elif name == "search_across_tables":
                return await self._search_across_tables_impl(arguments)
            elif name == "insert_data":
                return await self._insert_data_impl(arguments)
            elif name == "update_data":
                return await self._update_data_impl(arguments)
            elif name == "delete_data":
                return await self._delete_data_impl(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def _list_tables_impl(self) -> List[TextContent]:
        """List all tables in the database with intelligent discovery"""
        try:
            # Try to query Supabase information schema
            response = self.supabase.client.rpc('get_tables').execute()
            
            # If RPC doesn't exist, provide helpful guidance
            if not response.data:
                result = """# Table Discovery Not Configured

To enable automatic table discovery, please run this SQL in your Supabase SQL Editor:

```sql
CREATE OR REPLACE FUNCTION get_tables()
RETURNS TABLE(schema_name text, table_name text)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT schemaname::text, tablename::text
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY schemaname, tablename;
$$;
```

After creating this function, I'll be able to automatically discover all your tables.

**Alternative:** If you know your table names, you can:
1. Use `describe_table` with the table name to see its structure
2. Use `query_table` to search within specific tables
3. Use `search_across_tables` with specific table names
"""
                return [TextContent(type="text", text=result)]
            
            # Format results if RPC works
            tables = response.data
            result = f"# Found {len(tables)} tables in your Supabase database:\n\n"

            # Group by schema
            schemas = {}
            for table in tables:
                schema = table.get('schema_name', 'public')
                table_name = table.get('table_name', table)
                if schema not in schemas:
                    schemas[schema] = []
                schemas[schema].append(table_name)

            for schema, table_list in schemas.items():
                result += f"\n## Schema: `{schema}`\n"
                for table_name in table_list:
                    result += f"- **{table_name}** (use as `{schema}.{table_name}`)\n"
            
            result += "\n**Next steps:**\n"
            result += "- Use `describe_table` to see the structure of any table\n"
            result += "- Use `query_table` to search within specific tables\n"
            result += "- Use `search_across_tables` to search multiple tables at once"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            result = f"""# Table Discovery Error

**Error:** {str(e)}

This likely means the `get_tables()` function hasn't been created yet.

**To fix this, run this SQL in your Supabase SQL Editor:**

```sql
CREATE OR REPLACE FUNCTION get_tables()
RETURNS TABLE(schema_name text, table_name text)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT schemaname::text, tablename::text
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY schemaname, tablename;
$$;
```

**Manual approach:** If you know your table names:
1. Use `describe_table` with the table name
2. Use `query_table` to search within tables
3. Use `search_across_tables` with specific table names
"""
            return [TextContent(type="text", text=result)]
    
    async def _describe_table_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Describe the schema of a table with intelligent analysis"""
        table_name = args["table_name"]
        
        try:
            # Try to query the table and inspect the first few rows
            response = self.supabase.client.table(table_name).select("*").limit(3).execute()
            
            if not response.data or len(response.data) == 0:
                return [TextContent(type="text", text=f"# Table: {table_name}\n\n**Status:** Table exists but is empty. Cannot determine schema.")]
            
            # Analyze the data
            sample_rows = response.data
            columns = list(sample_rows[0].keys())
            
            result = f"# Schema for table: **{table_name}**\n\n"
            result += f"**Columns ({len(columns)}):**\n\n"
            
            # Analyze each column
            for col in columns:
                # Get sample values and determine type
                values = [row.get(col) for row in sample_rows if row.get(col) is not None]
                col_type = "unknown"
                sample_value = "No data"
                
                if values:
                    sample_value = str(values[0])
                    if len(sample_value) > 100:
                        sample_value = sample_value[:100] + "..."
                    
                    # Determine type
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
            result += f"- Sort results: `query_table` with `order_by`\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"# Error describing table '{table_name}'\n\n**Error:** {str(e)}\n\n**Possible causes:**\n- Table doesn't exist\n- Permission denied\n- Network issue\n\n**Try:** Check table name or use `list_tables` first")]
    
    async def _query_table_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Query a table with flexible filters and intelligent formatting"""
        table_name = args["table_name"]
        search_column = args.get("search_column")
        search_term = args.get("search_term")
        filters = args.get("filters", {})
        min_score = args.get("min_score")
        order_by = args.get("order_by")
        order_desc = args.get("order_desc", True)
        limit = args.get("limit", 20)
        
        try:
            # Build query
            query = self.supabase.client.table(table_name).select("*")
            
            # Text search
            if search_column and search_term:
                query = query.ilike(search_column, f"%{search_term}%")
            
            # Exact match filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            # Score filter
            if min_score:
                query = query.gte("score", min_score)
            
            # Ordering
            if order_by:
                query = query.order(order_by, desc=order_desc)
            
            # Limit
            query = query.limit(limit)
            
            # Execute
            response = query.execute()
            results = response.data
            
            # Format results intelligently
            result = f"# Query Results from '{table_name}'\n\n"
            result += f"**Found {len(results)} results**\n\n"
            
            if len(results) == 0:
                result += "**No results found** with the given filters.\n\n"
                result += "**Suggestions:**\n"
                result += "- Try different search terms\n"
                result += "- Remove some filters\n"
                result += "- Use `describe_table` to see available columns\n"
                return [TextContent(type="text", text=result)]
            
            # Display results with smart formatting
            for i, row in enumerate(results, 1):
                result += f"## Result {i}\n\n"
                
                # Show all columns with smart truncation
                for key, value in row.items():
                    if value is not None:
                        display_value = str(value)
                        if len(display_value) > 300:
                            display_value = display_value[:300] + "..."
                        result += f"**{key}:** {display_value}\n\n"
                
                result += "---\n\n"
            
            # Add helpful suggestions
            if len(results) == limit:
                result += f"**Note:** Showing first {limit} results. Use `limit` parameter to get more.\n\n"
            
            result += "**Next steps:**\n"
            result += "- Use `search_across_tables` to search multiple tables\n"
            result += "- Refine filters for more specific results\n"
            result += "- Use `describe_table` to understand the data better\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"# Error querying table '{table_name}'\n\n**Error:** {str(e)}\n\n**Troubleshooting:**\n- Check table name with `list_tables`\n- Verify column names with `describe_table`\n- Check filter values and types")]
    
    async def _search_across_tables_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Search across multiple tables with intelligent text detection"""
        search_term = args["search_term"]
        tables = args.get("tables")
        limit_per_table = args.get("limit_per_table", 10)

        # If no tables specified, try to get them dynamically
        if not tables:
            try:
                response = self.supabase.client.rpc('get_tables').execute()
                if response.data:
                    # Handle both old format (table_name only) and new format (schema + table)
                    tables = []
                    for table in response.data:
                        if isinstance(table, dict):
                            schema = table.get('schema_name', 'public')
                            table_name = table.get('table_name')
                            # Use schema-qualified name
                            tables.append(f"{schema}.{table_name}" if schema != 'public' else table_name)
                        else:
                            tables.append(table)
                else:
                    return [TextContent(type="text", text="# No Tables Specified\n\nPlease provide a list of table names to search, or create the `get_tables()` function in Supabase for automatic discovery.\n\n**Example:** Use `search_across_tables` with `tables: ['your_table_1', 'your_table_2']`")]
            except Exception as e:
                return [TextContent(type="text", text=f"# Cannot Auto-Discover Tables\n\n**Error:** {str(e)}\n\nPlease provide table names explicitly using the `tables` parameter.\n\n**Example:** `search_across_tables` with `tables: ['your_table_1', 'your_table_2']`")]
        
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
                
                # Find text columns intelligently
                text_columns = []
                sample_row = sample.data[0]
                
                for key, value in sample_row.items():
                    if isinstance(value, str) and len(value) > 5:  # Likely a text column
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
                    except Exception as e:
                        continue  # Skip problematic columns
                
                # Remove duplicates by ID
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
                        # Show relevant fields that contain the search term
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
        result += "**Next steps:**\n"
        result += "- Use `query_table` for more specific searches\n"
        result += "- Use `describe_table` to understand table structure\n"
        result += "- Refine search terms for better results\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _insert_data_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Insert data implementation"""
        table_name = args["table_name"]
        data = args["data"]
        
        try:
            result = await self.supabase.insert_data(table_name, data)
            return [TextContent(type="text", text=f"# Insert Successful\n\n**Table:** {table_name}\n**Data:** {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"# Insert Failed\n\n**Error:** {str(e)}")]
    
    async def _update_data_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Update data implementation"""
        table_name = args["table_name"]
        data = args["data"]
        filters = args["filters"]
        
        try:
            result = await self.supabase.update_data(table_name, data, filters)
            return [TextContent(type="text", text=f"# Update Successful\n\n**Table:** {table_name}\n**Updated rows:** {len(result)}\n**Data:** {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"# Update Failed\n\n**Error:** {str(e)}")]
    
    async def _delete_data_impl(self, args: Dict[str, Any]) -> List[TextContent]:
        """Delete data implementation"""
        table_name = args["table_name"]
        filters = args["filters"]
        
        try:
            result = await self.supabase.delete_data(table_name, filters)
            return [TextContent(type="text", text=f"# Delete Successful\n\n**Table:** {table_name}\n**Deleted rows:** {len(result)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"# Delete Failed\n\n**Error:** {str(e)}")]
    
    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server
