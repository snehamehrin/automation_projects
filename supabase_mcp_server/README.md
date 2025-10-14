# Supabase MCP Server

A Model Context Protocol (MCP) server that provides intelligent access to your Supabase database through natural language queries in Claude Desktop.

## Features

- **Dynamic Table Discovery** - Automatically discover and query any table in your database
- **Intelligent Search** - Search across multiple tables with natural language
- **Flexible Querying** - Filter, sort, and limit results with ease
- **Schema Inspection** - Understand your data structure on the fly
- **CRUD Operations** - Insert, update, and delete data through MCP tools

## Project Structure

```
supabase_mcp_server/
├── server.py              # Main MCP server entry point
├── run_server.sh          # Server startup script
├── src/
│   └── supabase_mcp/
│       ├── config.py      # Configuration management
│       ├── mcp_tools.py   # MCP tool implementations
│       └── supabase_client.py  # Supabase client wrapper
├── examples/              # Example usage scripts
├── tests/                 # Test suite
├── tests_backup/          # Additional test files
├── docs/                  # Documentation
├── venv/                  # Virtual environment
└── .env                   # Environment variables (not in git)
```

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Dependencies are already installed
```

### 2. Configure Environment

Your `.env` file should contain:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Test the Server

```bash
source venv/bin/activate
python tests_backup/test_mcp_server.py
```

### 4. Connect to Claude Desktop

The server is already configured in Claude Desktop at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Configuration:
```json
{
  "mcpServers": {
    "supabase": {
      "command": "/path/to/your/project/run_server.sh"
    }
  }
}
```

Restart Claude Desktop to connect.

## Available MCP Tools

### 1. list_tables
List all tables in your Supabase database.

### 2. describe_table
Get the schema and structure of a specific table.

**Example:** "Describe the brand_reddit_posts_comments table"

### 3. query_table
Query a table with flexible filters, sorting, and limits.

**Example:** "Show me the top 10 posts from the reddit_posts table"

### 4. search_across_tables
Search for a term across multiple tables at once.

**Example:** "Search for 'Knix' across all tables"

### 5. insert_data
Insert new records into a table.

### 6. update_data
Update existing records based on filters.

### 7. delete_data
Delete records from a table based on filters.

## Usage Examples

Once connected to Claude Desktop, you can ask:

- "What tables are in my database?"
- "Show me the schema for the users table"
- "Find all posts about 'bras' in the reddit_posts table"
- "Search for 'Knix' across all tables"
- "Show me the top 20 highest scoring posts"

## Troubleshooting

### Server Won't Connect
- Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
- Verify `.env` file has correct credentials
- Ensure virtual environment is activated

### Database Connection Issues
- Verify Supabase URL and key in `.env`
- Check Supabase project is active
- Test connection: `python tests_backup/test_mcp_server.py`

## Additional Documentation

- See `docs/` folder for detailed guides
- Check `examples/` for usage patterns

## License

MIT
