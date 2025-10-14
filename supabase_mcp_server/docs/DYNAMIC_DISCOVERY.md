# Dynamic Discovery MCP Server

## 🎯 Overview

The Dynamic Discovery MCP Server is an intelligent Supabase connector that automatically discovers your database structure and provides flexible querying capabilities. Instead of hardcoding specific queries, it adapts to your database schema and lets Claude figure out the best way to find the data you need.

## 🧠 How It Works

### The Smart Discovery Process

1. **Table Discovery**: Automatically finds all tables in your Supabase database
2. **Schema Analysis**: Intelligently analyzes table structure and data types
3. **Text Detection**: Identifies which columns contain searchable text
4. **Flexible Querying**: Provides multiple ways to search and filter data
5. **Cross-Table Search**: Searches across multiple tables simultaneously

### Example Workflow

**You ask:** "Find Reddit posts about Knix"

**Behind the scenes:**
1. Claude calls `list_tables()` → Discovers available tables
2. Claude calls `describe_table("reddit_posts")` → Understands the schema
3. Claude calls `query_table()` with smart filters → Gets relevant results
4. Claude presents formatted results with suggestions

## 🛠️ Available Tools

### 1. `list_tables`
**Purpose**: Discover all available tables in your database

**What it does**:
- Attempts to query the database schema
- Provides fallback guidance if schema access isn't available
- Suggests common table names based on your project

**Example output**:
```
# Available Tables in Your Supabase Database

Common tables in your database likely include:
- reddit_posts
- reddit_comments  
- brand_reddit_posts_comments
- reddit_brand_analysis_results
- prospects
```

### 2. `describe_table`
**Purpose**: Analyze the structure and content of any table

**What it does**:
- Examines sample data to determine column types
- Shows example values for each column
- Provides query suggestions based on the schema

**Example output**:
```
# Schema for table: reddit_posts

Columns (8):
- title (text)
  Sample: "Knix period underwear review - game changer!"

- body (text)  
  Sample: "I've been using Knix for 3 months now and..."

- score (integer)
  Sample: 42

- subreddit (text)
  Sample: "ABraThatFits"
```

### 3. `query_table`
**Purpose**: Flexible querying with multiple filter options

**Parameters**:
- `table_name`: Table to query
- `search_column`: Column to search in (for text search)
- `search_term`: Text to search for (case-insensitive)
- `filters`: Exact match filters
- `min_score`: Minimum score/upvotes
- `order_by`: Column to sort by
- `limit`: Maximum results

**Example**:
```json
{
  "table_name": "reddit_posts",
  "search_column": "title",
  "search_term": "Knix",
  "min_score": 10,
  "order_by": "score",
  "limit": 20
}
```

### 4. `search_across_tables`
**Purpose**: Search for terms across multiple tables simultaneously

**What it does**:
- Automatically detects text columns in each table
- Searches all text columns for the term
- Removes duplicates and formats results
- Provides suggestions for next steps

**Example**:
```json
{
  "search_term": "Knix",
  "tables": ["reddit_posts", "reddit_comments", "brand_reddit_posts_comments"],
  "limit_per_table": 10
}
```

## 🎯 Use Cases

### 1. Brand Research
**Query**: "Find all mentions of Knix in Reddit posts"
**Process**: 
- Discovers `reddit_posts` table
- Analyzes schema to find text columns
- Searches `title` and `body` columns
- Returns formatted results with context

### 2. Sentiment Analysis
**Query**: "Show me negative reviews about period underwear"
**Process**:
- Identifies relevant tables
- Searches for negative keywords
- Filters by product category
- Provides structured results for analysis

### 3. Competitive Intelligence
**Query**: "Compare mentions of different period underwear brands"
**Process**:
- Searches across multiple tables
- Groups results by brand
- Provides comparative insights
- Suggests deeper analysis

## 🔧 Advanced Features

### Intelligent Text Detection
The server automatically identifies which columns contain searchable text by:
- Analyzing sample data
- Detecting string columns with meaningful content
- Excluding system fields and IDs

### Smart Result Formatting
Results are formatted with:
- Clear section headers
- Truncated long text with "..." indicators
- Helpful suggestions for next steps
- Error handling with troubleshooting tips

### Flexible Filtering
Supports multiple filter types:
- **Text search**: Case-insensitive LIKE queries
- **Exact matches**: Equality filters
- **Range filters**: Minimum/maximum values
- **Sorting**: Ascending/descending by any column

## 🚀 Getting Started

### 1. Set Up Your Environment
```bash
cp env.example .env
# Add your Supabase credentials
```

### 2. Run the Server
```bash
python server.py
```

### 3. Connect to Claude
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "supabase-intelligence": {
      "command": "python",
      "args": ["/path/to/supabase_mcp_server/server.py"]
    }
  }
}
```

### 4. Start Querying
Ask Claude natural language questions like:
- "What tables do I have in my database?"
- "Show me the structure of the reddit_posts table"
- "Find all posts about Knix with high scores"
- "Search for period underwear mentions across all tables"

## 💡 Best Practices

### 1. Start with Discovery
Always begin by exploring your database:
- Use `list_tables` to see what's available
- Use `describe_table` to understand structure
- Use `search_across_tables` for broad searches

### 2. Refine Your Queries
- Start broad, then narrow down
- Use multiple filters for precise results
- Experiment with different search terms

### 3. Leverage Suggestions
The server provides helpful suggestions:
- Next steps after each query
- Troubleshooting for errors
- Optimization tips for better results

## 🔍 Troubleshooting

### Common Issues

**"Table not found"**
- Use `list_tables` to see available tables
- Check table name spelling
- Verify database permissions

**"No results found"**
- Try broader search terms
- Remove some filters
- Check if table has data

**"Permission denied"**
- Verify Supabase API key
- Check Row Level Security policies
- Ensure proper database access

### Getting Help

The server provides contextual help:
- Error messages include troubleshooting steps
- Results include suggestions for next actions
- Schema analysis shows available query options

## 🎉 Benefits

### For Users
- **No SQL knowledge required**: Ask questions in natural language
- **Automatic discovery**: No need to know table names or structure
- **Flexible querying**: Multiple ways to find the same data
- **Smart suggestions**: Always know what to do next

### For Developers
- **Schema-agnostic**: Works with any Supabase database
- **Extensible**: Easy to add new query types
- **Robust**: Handles errors gracefully
- **Maintainable**: Clean, well-documented code

This dynamic approach makes your Supabase data accessible to anyone, regardless of their technical background, while providing powerful querying capabilities for complex analysis tasks.
