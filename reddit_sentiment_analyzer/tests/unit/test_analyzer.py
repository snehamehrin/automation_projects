"""
Unit tests for the Reddit Sentiment Analyzer core functionality.

This module tests the main analyzer class and its methods.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData, AnalysisResult


class TestRedditSentimentAnalyzer:
    """Test cases for RedditSentimentAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, analyzer_with_mocks):
        """Test analyzer initialization."""
        assert analyzer_with_mocks._initialized is True
        assert analyzer_with_mocks.google_sheets is not None
        assert analyzer_with_mocks.apify is not None
        assert analyzer_with_mocks.openai is not None
        assert analyzer_with_mocks.data_processor is not None
    
    @pytest.mark.asyncio
    async def test_analyze_brand_success(self, analyzer_with_mocks, sample_brand_data):
        """Test successful brand analysis."""
        result = await analyzer_with_mocks.analyze_brand(sample_brand_data)
        
        assert isinstance(result, AnalysisResult)
        assert result.brand_name == sample_brand_data.name
        assert result.brand_category == sample_brand_data.category
        assert result.company_url == sample_brand_data.company_url
        assert result.total_posts > 0
        assert result.key_insight != ""
        assert result.html_report != ""
    
    @pytest.mark.asyncio
    async def test_analyze_brand_without_initialization(self, sample_brand_data):
        """Test brand analysis without initialization."""
        analyzer = RedditSentimentAnalyzer()
        
        # Should automatically initialize
        result = await analyzer.analyze_brand(sample_brand_data)
        assert isinstance(result, AnalysisResult)
    
    @pytest.mark.asyncio
    async def test_analyze_brands_batch(self, analyzer_with_mocks):
        """Test batch brand analysis."""
        brands = [
            BrandData(name="Brand 1", category="Category 1"),
            BrandData(name="Brand 2", category="Category 2")
        ]
        
        results = await analyzer_with_mocks.analyze_brands_batch(brands)
        
        assert len(results) == 2
        assert all(isinstance(result, AnalysisResult) for result in results)
        assert results[0].brand_name == "Brand 1"
        assert results[1].brand_name == "Brand 2"
    
    @pytest.mark.asyncio
    async def test_analyze_from_google_sheets(self, analyzer_with_mocks):
        """Test analysis from Google Sheets."""
        sheet_id = "test_sheet_id"
        
        results = await analyzer_with_mocks.analyze_from_google_sheets(sheet_id)
        
        assert len(results) == 1  # Based on mock data
        assert isinstance(results[0], AnalysisResult)
        assert results[0].brand_name == "Test Brand"
    
    def test_generate_search_query(self, analyzer_with_mocks, sample_brand_data):
        """Test search query generation."""
        query = analyzer_with_mocks._generate_search_query(sample_brand_data)
        
        assert "site:reddit.com" in query
        assert sample_brand_data.name in query
        assert sample_brand_data.category in query
        assert "review" in query.lower()
    
    def test_generate_search_query_without_category(self, analyzer_with_mocks):
        """Test search query generation without category."""
        brand_data = BrandData(name="Test Brand")
        query = analyzer_with_mocks._generate_search_query(brand_data)
        
        assert "site:reddit.com" in query
        assert "Test Brand" in query
        assert "review" in query.lower()
    
    @pytest.mark.asyncio
    async def test_search_reddit_urls(self, analyzer_with_mocks):
        """Test Reddit URL search."""
        search_query = "site:reddit.com Test Brand review"
        
        urls = await analyzer_with_mocks._search_reddit_urls(search_query)
        
        assert len(urls) == 1
        assert "reddit.com" in urls[0]
    
    @pytest.mark.asyncio
    async def test_scrape_reddit_content(self, analyzer_with_mocks):
        """Test Reddit content scraping."""
        reddit_urls = ["https://reddit.com/r/test/comments/abc123"]
        
        posts = await analyzer_with_mocks._scrape_reddit_content(reddit_urls)
        
        assert len(posts) == 1
        assert posts[0]["id"] == "abc123"
        assert posts[0]["text"] == "This is a test post about the brand."
    
    @pytest.mark.asyncio
    async def test_process_reddit_data(self, analyzer_with_mocks, sample_brand_data):
        """Test Reddit data processing."""
        raw_posts = [
            {
                "id": "post1",
                "text": "This is a test post about the brand.",
                "dataType": "post",
                "title": "Test Post",
                "communityName": "test",
                "upVotes": 10,
                "createdAt": "2024-01-15T10:30:00Z"
            }
        ]
        
        processed_posts = await analyzer_with_mocks._process_reddit_data(raw_posts, sample_brand_data)
        
        assert len(processed_posts) == 1
        assert processed_posts[0].brand_name == sample_brand_data.name
        assert processed_posts[0].company_url == sample_brand_data.company_url
    
    @pytest.mark.asyncio
    async def test_generate_ai_analysis(self, analyzer_with_mocks, sample_brand_data):
        """Test AI analysis generation."""
        from src.data.models import RedditPost, DataType
        
        posts = [
            RedditPost(
                id="post1",
                text="This is a test post about the brand.",
                data_type=DataType.POST,
                brand_name=sample_brand_data.name
            )
        ]
        
        analysis_result = await analyzer_with_mocks._generate_ai_analysis(posts, sample_brand_data)
        
        assert "brand_name" in analysis_result
        assert "key_insight" in analysis_result
        assert "html_report" in analysis_result
        assert analysis_result["brand_name"] == sample_brand_data.name
    
    @pytest.mark.asyncio
    async def test_close(self, analyzer_with_mocks):
        """Test analyzer cleanup."""
        await analyzer_with_mocks.close()
        assert analyzer_with_mocks._initialized is False
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analyze_brand(self, sample_brand_data):
        """Test error handling in brand analysis."""
        # Create analyzer with failing services
        mock_google_sheets = AsyncMock()
        mock_google_sheets.initialize = AsyncMock(side_effect=Exception("Service error"))
        
        analyzer = RedditSentimentAnalyzer(google_sheets_service=mock_google_sheets)
        
        with pytest.raises(Exception):
            await analyzer.analyze_brand(sample_brand_data)
    
    @pytest.mark.asyncio
    async def test_empty_reddit_urls(self, analyzer_with_mocks, sample_brand_data):
        """Test handling of empty Reddit URLs."""
        # Mock empty search results
        analyzer_with_mocks.apify.google_search = AsyncMock(return_value={"organicResults": []})
        
        result = await analyzer_with_mocks.analyze_brand(sample_brand_data)
        
        assert isinstance(result, AnalysisResult)
        assert result.total_posts == 0
    
    @pytest.mark.asyncio
    async def test_scraping_failure(self, analyzer_with_mocks, sample_brand_data):
        """Test handling of scraping failures."""
        # Mock scraping failure
        analyzer_with_mocks.apify.scrape_reddit = AsyncMock(side_effect=Exception("Scraping failed"))
        
        with pytest.raises(Exception):
            await analyzer_with_mocks.analyze_brand(sample_brand_data)
