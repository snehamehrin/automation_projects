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
├── requirements.txt       # Dependencies
├── README.md              # This file
├── src/
│   └── supabase_mcp/
│       ├── config.py      # Configuration management
│       ├── mcp_tools.py   # MCP tool implementations
│       └── supabase_client.py  # Supabase client wrapper
├── tests/                 # Test suite
├── venv/                  # Virtual environment
└── .env                   # Environment variables (not in git)
```

## Quick Start

### Option A: Run Locally (Current Setup)

1. **Test the Server**
```bash
source venv/bin/activate
pytest tests/
```

2. **Claude Desktop Config** (already configured)
```json
{
  "mcpServers": {
    "supabase": {
      "command": "/path/to/run_server.sh"
    }
  }
}
```

### Option B: Deploy to VPS (Recommended)

1. **Edit deploy.sh** with your VPS details
2. **Run deployment**
```bash
./deploy.sh
```

3. **Configure .env on VPS**
```bash
ssh user@your_vps
cd ~/supabase_mcp_server
nano .env  # Add SUPABASE_URL and SUPABASE_KEY
sudo systemctl restart supabase-mcp
```

4. **Update Claude Desktop Config**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "http://your_vps_ip:8000/sse"
    }
  }
}
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

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
- Run tests: `pytest tests/`

## License

MIT
