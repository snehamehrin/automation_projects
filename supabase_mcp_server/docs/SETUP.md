# Setup Guide

## Prerequisites

- Python 3.8 or higher
- Supabase account and project
- Claude Desktop or MCP-compatible client

## Installation

### 1. Clone or Download

```bash
git clone <repository-url>
cd supabase_mcp_server
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using pip with development dependencies
pip install -e ".[dev]"
```

### 3. Environment Configuration

Copy the example environment file and configure your Supabase credentials:

```bash
cp env.example .env
```

Edit `.env` with your Supabase project details:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### 4. Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to Settings > API
3. Copy the following:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (optional, for admin operations)

## Running the Server

### Development Mode

```bash
python server.py
```

### Production Mode

```bash
# Install as package
pip install -e .

# Run using the installed script
supabase-mcp-server
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/supabase_mcp
```

## Integration with Claude Desktop

### 1. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "supabase": {
      "command": "python",
      "args": ["/path/to/supabase_mcp_server/server.py"],
      "env": {
        "SUPABASE_URL": "https://your-project-id.supabase.co",
        "SUPABASE_KEY": "your-anon-key-here"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the new MCP server.

### 3. Verify Connection

In Claude, you should now be able to use Supabase tools. Try asking:

> "Can you query the users table from my Supabase database?"

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path and virtual environment

2. **"Connection failed" errors**
   - Verify Supabase URL and keys in `.env`
   - Check network connectivity
   - Ensure Supabase project is active

3. **"Permission denied" errors**
   - Check Row Level Security (RLS) policies in Supabase
   - Verify the API key has appropriate permissions
   - Consider using service role key for admin operations

4. **"Table not found" errors**
   - Verify table names are correct
   - Check if tables exist in your Supabase project
   - Ensure proper schema permissions

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
python server.py
```

### Getting Help

- Check the [API Documentation](API.md) for detailed tool usage
- Review Supabase documentation for database-specific issues
- Check the test files for usage examples
