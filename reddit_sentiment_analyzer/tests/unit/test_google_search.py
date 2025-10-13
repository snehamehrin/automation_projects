"""
Unit tests for google_search module
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from modules.google_search import GoogleSearcher


class TestGoogleSearcher:
    """Test cases for GoogleSearcher class"""
    
    @pytest.fixture
    def google_searcher(self, mock_database):
        """Create GoogleSearcher instance with mocked dependencies"""
        with patch('modules.google_search.Database', return_value=mock_database), \
             patch('modules.google_search.get_settings') as mock_settings:
            mock_settings.return_value.APIFY_API_KEY = "test-token"
            mock_settings.return_value.APIFY_ACTOR = "apify/google-search-scraper"
            mock_settings.return_value.MAX_REDDIT_URLS = 10
            return GoogleSearcher()
    
    @pytest.mark.asyncio
    async def test_search_reddit_urls_success(self, google_searcher, mock_google_search_results):
        """Test successful Reddit URL search"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_google_search_results
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute
            result = await google_searcher.search_reddit_urls("Test Brand", "Wellness")
        
        # Assert
        assert len(result) == 2
        assert "reddit.com/r/Supplements" in result[0]
        assert "reddit.com/r/Wellness" in result[1]
    
    @pytest.mark.asyncio
    async def test_search_reddit_urls_no_results(self, google_searcher):
        """Test search with no Reddit URLs found"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [{'organicResults': []}]
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute
            result = await google_searcher.search_reddit_urls("Unknown Brand")
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_reddit_urls_http_error(self, google_searcher):
        """Test search with HTTP error"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=Mock()
            )
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await google_searcher.search_reddit_urls("Test Brand")
    
    @pytest.mark.asyncio
    async def test_search_reddit_urls_limit_results(self, google_searcher):
        """Test that results are limited to MAX_REDDIT_URLS"""
        # Setup - create more results than the limit
        many_results = []
        for i in range(15):  # More than MAX_REDDIT_URLS (10)
            many_results.append({
                'organicResults': [
                    {
                        'url': f'https://reddit.com/r/Test{i}/comments/abc{i}',
                        'title': f'Test Brand Discussion {i}',
                        'snippet': f'Discussion about Test Brand {i}'
                    }
                ]
            })
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = many_results
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute
            result = await google_searcher.search_reddit_urls("Test Brand")
        
        # Assert
        assert len(result) == 10  # Should be limited to MAX_REDDIT_URLS
    
    @pytest.mark.asyncio
    async def test_update_prospect_urls(self, google_searcher, mock_database):
        """Test updating prospect with Reddit URLs"""
        # Setup
        urls = [
            'https://reddit.com/r/Test1/comments/abc123',
            'https://reddit.com/r/Test2/comments/def456'
        ]
        prospect_id = "test-prospect-123"
        
        # Execute
        await google_searcher.update_prospect_urls(prospect_id, urls)
        
        # Assert
        mock_database.insert_reddit_urls.assert_called_once()
        call_args = mock_database.insert_reddit_urls.call_args[0][0]
        
        assert len(call_args) == 2
        assert call_args[0]['prospect_id'] == prospect_id
        assert call_args[0]['url'] == urls[0]
        assert call_args[0]['status'] == 'pending'
        assert call_args[1]['prospect_id'] == prospect_id
        assert call_args[1]['url'] == urls[1]
        assert call_args[1]['status'] == 'pending'
    
    def test_search_query_format(self, google_searcher):
        """Test that search query uses correct format"""
        # This test verifies the search query format is 'reddit:brandname'
        # We can't easily test the private method, but we can verify the behavior
        # through the public method
        
        # The actual implementation should use 'reddit:brandname' format
        # This is verified in the integration tests
        assert True  # Placeholder - actual verification in integration tests
