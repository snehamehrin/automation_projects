"""
Unit tests for database module
"""

import pytest
from unittest.mock import Mock, patch
from database.db import Database


class TestDatabase:
    """Test cases for Database class"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        return Mock()
    
    @pytest.fixture
    def database(self, mock_supabase_client):
        """Create Database instance with mocked Supabase client"""
        with patch('database.db.create_client', return_value=mock_supabase_client), \
             patch('database.db.get_settings') as mock_settings:
            mock_settings.return_value.SUPABASE_URL = "test-url"
            mock_settings.return_value.SUPABASE_KEY = "test-key"
            return Database()
    
    @pytest.mark.asyncio
    async def test_get_prospect_by_name_found(self, database, mock_supabase_client):
        """Test getting existing prospect by name"""
        # Setup
        mock_response = Mock()
        mock_response.data = [{'id': '123', 'brand_name': 'Test Brand'}]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.get_prospect_by_name("Test Brand")
        
        # Assert
        assert result == {'id': '123', 'brand_name': 'Test Brand'}
        mock_supabase_client.table.assert_called_with('prospects')
    
    @pytest.mark.asyncio
    async def test_get_prospect_by_name_not_found(self, database, mock_supabase_client):
        """Test getting non-existent prospect by name"""
        # Setup
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.get_prospect_by_name("Non-existent Brand")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_prospect(self, database, mock_supabase_client):
        """Test creating new prospect"""
        # Setup
        prospect_data = {'brand_name': 'New Brand', 'industry_category': 'Wellness'}
        mock_response = Mock()
        mock_response.data = [{'id': '456', **prospect_data}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.create_prospect(prospect_data)
        
        # Assert
        assert result == {'id': '456', **prospect_data}
        mock_supabase_client.table.assert_called_with('prospects')
        mock_supabase_client.table.return_value.insert.assert_called_with(prospect_data)
    
    @pytest.mark.asyncio
    async def test_get_all_prospects(self, database, mock_supabase_client):
        """Test getting all prospects"""
        # Setup
        mock_response = Mock()
        mock_response.data = [
            {'id': '123', 'brand_name': 'Brand 1'},
            {'id': '456', 'brand_name': 'Brand 2'}
        ]
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.get_all_prospects()
        
        # Assert
        assert len(result) == 2
        assert result[0]['brand_name'] == 'Brand 1'
        assert result[1]['brand_name'] == 'Brand 2'
    
    @pytest.mark.asyncio
    async def test_update_prospect(self, database, mock_supabase_client):
        """Test updating prospect"""
        # Setup
        update_data = {'industry_category': 'Health'}
        mock_response = Mock()
        mock_response.data = [{'id': '123', 'brand_name': 'Test Brand', **update_data}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.update_prospect("123", update_data)
        
        # Assert
        assert result == {'id': '123', 'brand_name': 'Test Brand', **update_data}
        mock_supabase_client.table.return_value.update.assert_called_with(update_data)
        mock_supabase_client.table.return_value.update.return_value.eq.assert_called_with('id', "123")
    
    @pytest.mark.asyncio
    async def test_insert_reddit_urls(self, database, mock_supabase_client):
        """Test inserting Reddit URLs"""
        # Setup
        urls = [
            {'prospect_id': '123', 'url': 'https://reddit.com/r/test1', 'status': 'pending'},
            {'prospect_id': '123', 'url': 'https://reddit.com/r/test2', 'status': 'pending'}
        ]
        mock_response = Mock()
        mock_response.data = urls
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.insert_reddit_urls(urls)
        
        # Assert
        assert result == urls
        mock_supabase_client.table.assert_called_with('brand_google_reddit')
        mock_supabase_client.table.return_value.insert.assert_called_with(urls)
    
    @pytest.mark.asyncio
    async def test_get_reddit_urls(self, database, mock_supabase_client):
        """Test getting Reddit URLs for prospect"""
        # Setup
        mock_response = Mock()
        mock_response.data = [
            {'id': '1', 'prospect_id': '123', 'url': 'https://reddit.com/r/test1'},
            {'id': '2', 'prospect_id': '123', 'url': 'https://reddit.com/r/test2'}
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.get_reddit_urls("123")
        
        # Assert
        assert len(result) == 2
        assert result[0]['url'] == 'https://reddit.com/r/test1'
        assert result[1]['url'] == 'https://reddit.com/r/test2'
    
    @pytest.mark.asyncio
    async def test_insert_posts_comments_empty(self, database, mock_supabase_client):
        """Test inserting empty posts/comments list"""
        # Execute
        await database.insert_posts_comments([])
        
        # Assert - should not call Supabase
        mock_supabase_client.table.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_insert_posts_comments_small_batch(self, database, mock_supabase_client):
        """Test inserting small batch of posts/comments"""
        # Setup
        data = [
            {'id': '1', 'body': 'Test post 1'},
            {'id': '2', 'body': 'Test post 2'}
        ]
        mock_response = Mock()
        mock_response.data = data
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Execute
        await database.insert_posts_comments(data)
        
        # Assert
        mock_supabase_client.table.assert_called_with('brand_reddit_posts_comments')
        mock_supabase_client.table.return_value.insert.assert_called_with(data)
    
    @pytest.mark.asyncio
    async def test_insert_posts_comments_large_batch(self, database, mock_supabase_client):
        """Test inserting large batch of posts/comments (should be chunked)"""
        # Setup - create 1500 items (more than chunk size of 1000)
        data = [{'id': f'{i}', 'body': f'Test post {i}'} for i in range(1500)]
        mock_response = Mock()
        mock_response.data = data
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Execute
        await database.insert_posts_comments(data)
        
        # Assert - should be called twice (chunks of 1000 and 500)
        assert mock_supabase_client.table.return_value.insert.call_count == 2
        
        # Verify first chunk
        first_call = mock_supabase_client.table.return_value.insert.call_args_list[0][0][0]
        assert len(first_call) == 1000
        
        # Verify second chunk
        second_call = mock_supabase_client.table.return_value.insert.call_args_list[1][0][0]
        assert len(second_call) == 500
    
    @pytest.mark.asyncio
    async def test_insert_analysis_result(self, database, mock_supabase_client):
        """Test inserting analysis result"""
        # Setup
        result_data = {
            'brand_name': 'Test Brand',
            'key_insight': 'Test insight',
            'html_content': '<html>Test</html>',
            'analysis_date': '2024-01-15T12:00:00Z',
            'prospect_id': '123'
        }
        mock_response = Mock()
        mock_response.data = [{'id': 'analysis-123', **result_data}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Execute
        result = await database.insert_analysis_result(result_data)
        
        # Assert
        assert result == {'id': 'analysis-123', **result_data}
        mock_supabase_client.table.assert_called_with('reddit_brand_analysis_results')
        mock_supabase_client.table.return_value.insert.assert_called_with(result_data)

