#!/bin/bash
# MCP Server startup script

# Change to the server directory
cd /Users/snehamehrin/Desktop/automation_projects/supabase_mcp_server

# Load the virtual environment
source venv/bin/activate

# Run the server
exec python server.py
