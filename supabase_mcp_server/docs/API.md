# Supabase MCP Server API Documentation

## Overview

The Supabase MCP Server provides a set of tools that allow Claude to interact directly with Supabase databases through the Model Context Protocol (MCP).

## Available Tools

### 1. query_table

Query data from a Supabase table with optional filters and limits.

**Parameters:**
- `table_name` (string, required): Name of the table to query
- `select` (string, optional): Columns to select (default: "*")
- `filters` (object, optional): Key-value pairs for filtering rows
- `limit` (integer, optional): Maximum number of rows to return

**Example:**
```json
{
  "table_name": "users",
  "select": "id, email, name",
  "filters": {"active": true, "role": "admin"},
  "limit": 50
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Query successful. Found 5 rows:\n[{'id': 1, 'email': 'admin@example.com', 'name': 'Admin User'}, ...]"
}
```

### 2. insert_data

Insert new data into a Supabase table.

**Parameters:**
- `table_name` (string, required): Name of the table to insert into
- `data` (object, required): Data to insert

**Example:**
```json
{
  "table_name": "users",
  "data": {
    "email": "newuser@example.com",
    "name": "New User",
    "active": true
  }
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Insert successful: {'id': 123, 'email': 'newuser@example.com', 'name': 'New User', 'active': true}"
}
```

### 3. update_data

Update existing data in a Supabase table.

**Parameters:**
- `table_name` (string, required): Name of the table to update
- `data` (object, required): Data to update
- `filters` (object, required): Key-value pairs for filtering which rows to update

**Example:**
```json
{
  "table_name": "users",
  "data": {"active": false},
  "filters": {"email": "olduser@example.com"}
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Update successful. Updated 1 rows: [{'id': 456, 'email': 'olduser@example.com', 'active': false}]"
}
```

### 4. delete_data

Delete data from a Supabase table.

**Parameters:**
- `table_name` (string, required): Name of the table to delete from
- `filters` (object, required): Key-value pairs for filtering which rows to delete

**Example:**
```json
{
  "table_name": "users",
  "filters": {"active": false, "created_at": "2023-01-01"}
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Delete successful. Deleted 3 rows"
}
```

### 5. list_tables

List all tables in the Supabase database.

**Parameters:** None

**Example:**
```json
{}
```

**Response:**
```json
{
  "type": "text",
  "text": "Table listing requires admin API access. Please specify table names directly."
}
```

## Error Handling

All tools return error messages in the following format when operations fail:

```json
{
  "type": "text",
  "text": "Operation failed: [error message]"
}
```

Common error scenarios:
- Invalid table name
- Permission denied (RLS policies)
- Invalid data format
- Network connectivity issues
- Supabase service errors

## Security Considerations

- All operations respect Supabase Row Level Security (RLS) policies
- The server uses the configured Supabase key (anon or service role)
- Service role key provides admin access, anon key respects RLS
- All database operations are logged for audit purposes

## Rate Limiting

- Default query limit: 1000 rows per request
- Timeout: 30 seconds per operation
- These can be configured via environment variables
