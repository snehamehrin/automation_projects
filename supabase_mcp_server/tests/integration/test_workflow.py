"""
Integration tests for the complete MCP workflow
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
from src.supabase_mcp.supabase_client import SupabaseClient


class TestWorkflowIntegration:
    """Integration tests for the complete workflow"""
    
    @pytest.fixture
    def mock_tools(self):
        """Create tools instance with mocked dependencies"""
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            mock_client.return_value = Mock()
            tools = DynamicSupabaseMCPTools()
            tools.supabase = mock_client.return_value
            return tools
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_tools):
        """Test the complete workflow from discovery to query"""
        
        # Mock the supabase responses
        mock_tools.supabase.client.rpc.return_value.execute.return_value.data = None  # No RPC function
        mock_tools.supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {"id": 1, "title": "Test post", "body": "Test content", "score": 10}
        ]
        
        # Step 1: List tables (should provide guidance)
        result = await mock_tools._list_tables_impl()
        assert "Available Tables" in result[0].text
        assert "reddit_posts" in result[0].text
        
        # Step 2: Describe table
        result = await mock_tools._describe_table_impl({"table_name": "test_table"})
        assert "Schema for table" in result[0].text
        assert "Columns" in result[0].text
        
        # Step 3: Query table
        result = await mock_tools._query_table_impl({
            "table_name": "test_table",
            "search_column": "title",
            "search_term": "test",
            "limit": 5
        })
        assert "Query Results" in result[0].text
        assert "Found 1 results" in result[0].text
        
        # Step 4: Search across tables
        result = await mock_tools._search_across_tables_impl({
            "search_term": "test",
            "tables": ["test_table"],
            "limit_per_table": 5
        })
        assert "Search Results" in result[0].text
        assert "test" in result[0].text
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, mock_tools):
        """Test error handling throughout the workflow"""
        
        # Mock errors
        mock_tools.supabase.client.table.side_effect = Exception("Connection failed")
        
        # Test that errors are handled gracefully
        result = await mock_tools._describe_table_impl({"table_name": "nonexistent_table"})
        assert "Error describing table" in result[0].text
        assert "Connection failed" in result[0].text
        assert "Troubleshooting" in result[0].text
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, mock_tools):
        """Test handling of empty results"""
        
        # Mock empty results
        mock_tools.supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
        
        # Test empty table
        result = await mock_tools._describe_table_impl({"table_name": "empty_table"})
        assert "Table exists but is empty" in result[0].text
        
        # Test empty query results
        result = await mock_tools._query_table_impl({"table_name": "empty_table"})
        assert "No results found" in result[0].text
        assert "Suggestions" in result[0].text
