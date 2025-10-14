# Dynamic Supabase MCP Server

An intelligent Model Context Protocol (MCP) server that provides Claude with dynamic discovery and flexible access to Supabase database operations. No hardcoded queries needed - it automatically discovers your database structure and adapts to your schema.

## 🚀 Features

- **🧠 Dynamic Discovery**: Automatically discovers your database structure
- **🔍 Intelligent Search**: Smart text detection and cross-table searching
- **📊 Schema Analysis**: Analyzes table structure and data types automatically
- **🎯 Flexible Querying**: Multiple filter types and search options
- **🔄 Cross-Table Search**: Search across multiple tables simultaneously
- **💡 Smart Suggestions**: Provides helpful next steps and troubleshooting
- **🔒 Secure Connection**: Environment-based configuration with RLS support
- **🧪 Full Testing**: Comprehensive test suite with examples

## 📁 Project Structure

```
supabase_mcp_server/
├── src/supabase_mcp/          # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── supabase_client.py     # Supabase client wrapper
│   └── mcp_tools.py          # MCP tools implementation
├── tests/                     # Test suite
│   ├── test_supabase_client.py
│   └── test_mcp_tools.py
├── docs/                      # Documentation
│   ├── API.md
│   └── SETUP.md
├── examples/                  # Usage examples
│   └── basic_usage.py
├── server.py                  # Main server entry point
├── requirements.txt           # Dependencies
├── pyproject.toml            # Package configuration
└── README.md                 # This file
```

## ⚡ Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your Supabase credentials
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

## 🔧 Available Tools

### 🗂️ `list_tables`
**Dynamic Discovery**: Automatically finds all tables in your database
- Discovers schema without hardcoding
- Provides fallback guidance
- Suggests common table patterns

### 📋 `describe_table`
**Schema Analysis**: Intelligently analyzes table structure
- Examines sample data to determine types
- Shows example values for each column
- Provides query suggestions

### 🔍 `query_table`
**Flexible Querying**: Advanced search with multiple filter types
- Text search with case-insensitive matching
- Exact match filters
- Score/range filtering
- Custom sorting and limits

### 🔄 `search_across_tables`
**Cross-Table Search**: Search multiple tables simultaneously
- Automatically detects text columns
- Removes duplicates intelligently
- Provides comprehensive results

### ➕ `insert_data` / `update_data` / `delete_data`
**Data Manipulation**: Full CRUD operations with error handling

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Dynamic Discovery Guide](docs/DYNAMIC_DISCOVERY.md)** - How the intelligent discovery works
- **[Examples](examples/)** - Usage examples and patterns

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/supabase_mcp
```

## 🔒 Security

- Uses Supabase's built-in Row Level Security (RLS)
- Supports both anon and service role keys
- All operations respect Supabase permissions
- Environment-based configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
