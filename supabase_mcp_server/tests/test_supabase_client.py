"""
Tests for Supabase client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.supabase_mcp.supabase_client import SupabaseClient


class TestSupabaseClient:
    """Test cases for SupabaseClient"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch('src.supabase_mcp.supabase_client.get_settings') as mock:
            mock.return_value.supabase_url = "https://test.supabase.co"
            mock.return_value.supabase_key = "test-key"
            yield mock.return_value
    
    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance with mocked settings"""
        with patch('src.supabase_mcp.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            client = SupabaseClient()
            client.client = mock_client
            return client
    
    @pytest.mark.asyncio
    async def test_query_table(self, client):
        """Test query_table method"""
        # Mock response
        mock_response = Mock()
        mock_response.data = [{"id": 1, "name": "test"}]
        
        # Mock query chain
        client.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        # Test query
        result = await client.query_table("test_table", filters={"id": 1}, limit=10)
        
        assert result == [{"id": 1, "name": "test"}]
        client.client.table.assert_called_once_with("test_table")
    
    @pytest.mark.asyncio
    async def test_insert_data(self, client):
        """Test insert_data method"""
        # Mock response
        mock_response = Mock()
        mock_response.data = [{"id": 1, "name": "test"}]
        client.client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Test insert
        result = await client.insert_data("test_table", {"name": "test"})
        
        assert result == {"id": 1, "name": "test"}
        client.client.table.assert_called_once_with("test_table")
    
    @pytest.mark.asyncio
    async def test_update_data(self, client):
        """Test update_data method"""
        # Mock response
        mock_response = Mock()
        mock_response.data = [{"id": 1, "name": "updated"}]
        
        # Mock query chain
        client.client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        # Test update
        result = await client.update_data("test_table", {"name": "updated"}, {"id": 1})
        
        assert result == [{"id": 1, "name": "updated"}]
        client.client.table.assert_called_once_with("test_table")
    
    @pytest.mark.asyncio
    async def test_delete_data(self, client):
        """Test delete_data method"""
        # Mock response
        mock_response = Mock()
        mock_response.data = []
        
        # Mock query chain
        client.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response
        
        # Test delete
        result = await client.delete_data("test_table", {"id": 1})
        
        assert result == []
        client.client.table.assert_called_once_with("test_table")
