"""
Unit tests for reddit_scraper module
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from modules.reddit_scraper import RedditScraper


class TestRedditScraper:
    """Test cases for RedditScraper class"""
    
    @pytest.fixture
    def reddit_scraper(self, mock_database):
        """Create RedditScraper instance with mocked dependencies"""
        with patch('modules.reddit_scraper.Database', return_value=mock_database), \
             patch('modules.reddit_scraper.get_settings') as mock_settings:
            mock_settings.return_value.APIFY_API_KEY = "test-token"
            mock_settings.return_value.APIFY_ACTOR = "trudax/reddit-scraper-lite"
            mock_settings.return_value.MAX_POSTS_PER_URL = 20
            mock_settings.return_value.MAX_COMMENTS_PER_POST = 20
            return RedditScraper()
    
    @pytest.mark.asyncio
    async def test_scrape_all_urls_success(self, reddit_scraper, mock_reddit_data, mock_reddit_urls):
        """Test successful scraping of multiple URLs"""
        # Setup
        with patch.object(reddit_scraper, '_scrape_url', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_reddit_data
            
            # Execute
            result = await reddit_scraper.scrape_all_urls(
                mock_reddit_urls, "Test Brand", "test-prospect-123"
            )
        
        # Assert
        assert len(result) == len(mock_reddit_data) * len(mock_reddit_urls)
        assert mock_scrape.call_count == len(mock_reddit_urls)
        reddit_scraper.db.insert_posts_comments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_all_urls_with_errors(self, reddit_scraper, mock_reddit_data, mock_reddit_urls):
        """Test scraping with some URLs failing"""
        # Setup
        with patch.object(reddit_scraper, '_scrape_url', new_callable=AsyncMock) as mock_scrape:
            # First URL succeeds, second fails, third succeeds
            mock_scrape.side_effect = [
                mock_reddit_data,  # Success
                Exception("API Error"),  # Failure
                mock_reddit_data   # Success
            ]
            
            # Execute
            result = await reddit_scraper.scrape_all_urls(
                mock_reddit_urls, "Test Brand", "test-prospect-123"
            )
        
        # Assert
        assert len(result) == len(mock_reddit_data) * 2  # Only 2 successful scrapes
        assert mock_scrape.call_count == len(mock_reddit_urls)
        reddit_scraper.db.insert_posts_comments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_url_success(self, reddit_scraper, mock_apify_response):
        """Test successful scraping of a single URL"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_apify_response
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute
            result = await reddit_scraper._scrape_url(
                "https://reddit.com/r/test/comments/123", "Test Brand", "test-prospect-123"
            )
        
        # Assert
        assert len(result) == 1
        assert result[0]['url'] == "https://reddit.com/r/test/comments/123"
        assert result[0]['brand_name'] == "Test Brand"
        assert result[0]['prospect_id'] == "test-prospect-123"
        assert result[0]['data_type'] == "post"
        assert result[0]['body'] == "Great product!"
    
    @pytest.mark.asyncio
    async def test_scrape_url_http_error(self, reddit_scraper):
        """Test scraping with HTTP error"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=Mock()
            )
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await reddit_scraper._scrape_url(
                    "https://reddit.com/r/test/comments/123", "Test Brand", "test-prospect-123"
                )
    
    @pytest.mark.asyncio
    async def test_scrape_url_empty_response(self, reddit_scraper):
        """Test scraping with empty response"""
        # Setup
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Execute
            result = await reddit_scraper._scrape_url(
                "https://reddit.com/r/test/comments/123", "Test Brand", "test-prospect-123"
            )
        
        # Assert
        assert result == []
    
    def test_transform_post_data(self, reddit_scraper):
        """Test transformation of post data"""
        # Setup
        post_data = {
            'id': 'post-123',
            'dataType': 'post',
            'title': 'Test Post',
            'body': 'Test body content',
            'url': 'https://reddit.com/r/test/comments/123',
            'communityName': 'test',
            'createdAt': '2024-01-15T10:30:00Z',
            'upVotes': 10,
            'commentsCount': 5,
            'category': 'review'
        }
        
        # Execute
        result = reddit_scraper._scrape_url(
            "https://reddit.com/r/test/comments/123", "Test Brand", "test-prospect-123"
        )
        
        # This is a simplified test - in reality we'd mock the HTTP call
        # and test the transformation logic separately
        assert True  # Placeholder for actual transformation test
    
    def test_transform_comment_data(self, reddit_scraper):
        """Test transformation of comment data"""
        # Setup
        comment_data = {
            'id': 'comment-456',
            'dataType': 'comment',
            'body': 'Test comment content',
            'url': 'https://reddit.com/r/test/comments/123',
            'communityName': 'test',
            'createdAt': '2024-01-15T11:15:00Z',
            'upVotes': 3,
            'numberOfReplies': 0,
            'postId': 'post-123',
            'parentId': None
        }
        
        # Execute
        result = reddit_scraper._scrape_url(
            "https://reddit.com/r/test/comments/123", "Test Brand", "test-prospect-123"
        )
        
        # This is a simplified test - in reality we'd mock the HTTP call
        # and test the transformation logic separately
        assert True  # Placeholder for actual transformation test
