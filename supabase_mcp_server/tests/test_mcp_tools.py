"""
Tests for MCP tools
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.supabase_mcp.mcp_tools import SupabaseMCPTools


class TestSupabaseMCPTools:
    """Test cases for SupabaseMCPTools"""
    
    @pytest.fixture
    def tools(self):
        """Create tools instance with mocked dependencies"""
        with patch('src.supabase_mcp.mcp_tools.SupabaseClient') as mock_client:
            mock_client.return_value = Mock()
            tools = SupabaseMCPTools()
            tools.supabase = mock_client.return_value
            return tools
    
    @pytest.mark.asyncio
    async def test_query_table_tool(self, tools):
        """Test query_table tool"""
        # Mock supabase response
        tools.supabase.query_table = AsyncMock(return_value=[{"id": 1, "name": "test"}])
        
        # Test tool call
        result = await tools._query_table("test_table", filters={"id": 1})
        
        assert "Query successful" in result
        assert "Found 1 rows" in result
        tools.supabase.query_table.assert_called_once_with("test_table", "*", {"id": 1}, None)
    
    @pytest.mark.asyncio
    async def test_insert_data_tool(self, tools):
        """Test insert_data tool"""
        # Mock supabase response
        tools.supabase.insert_data = AsyncMock(return_value={"id": 1, "name": "test"})
        
        # Test tool call
        result = await tools._insert_data("test_table", {"name": "test"})
        
        assert "Insert successful" in result
        tools.supabase.insert_data.assert_called_once_with("test_table", {"name": "test"})
    
    @pytest.mark.asyncio
    async def test_update_data_tool(self, tools):
        """Test update_data tool"""
        # Mock supabase response
        tools.supabase.update_data = AsyncMock(return_value=[{"id": 1, "name": "updated"}])
        
        # Test tool call
        result = await tools._update_data("test_table", {"name": "updated"}, {"id": 1})
        
        assert "Update successful" in result
        assert "Updated 1 rows" in result
        tools.supabase.update_data.assert_called_once_with("test_table", {"name": "updated"}, {"id": 1})
    
    @pytest.mark.asyncio
    async def test_delete_data_tool(self, tools):
        """Test delete_data tool"""
        # Mock supabase response
        tools.supabase.delete_data = AsyncMock(return_value=[])
        
        # Test tool call
        result = await tools._delete_data("test_table", {"id": 1})
        
        assert "Delete successful" in result
        assert "Deleted 0 rows" in result
        tools.supabase.delete_data.assert_called_once_with("test_table", {"id": 1})
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tools):
        """Test error handling in tools"""
        # Mock supabase to raise exception
        tools.supabase.query_table = AsyncMock(side_effect=Exception("Database error"))
        
        # Test tool call
        result = await tools._query_table("test_table")
        
        assert "Query failed" in result
        assert "Database error" in result
