"""
Integration tests for the complete workflow
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


class TestWorkflowIntegration:
    """Integration tests for the complete brand analysis workflow"""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock all external dependencies"""
        with patch('modules.brand_selector.Database') as mock_db_class, \
             patch('modules.google_search.Database') as mock_db_class2, \
             patch('modules.reddit_scraper.Database') as mock_db_class3, \
             patch('modules.analysis.Database') as mock_db_class4, \
             patch('modules.google_search.get_settings') as mock_settings, \
             patch('modules.reddit_scraper.get_settings') as mock_settings2, \
             patch('modules.analysis.get_settings') as mock_settings3, \
             patch('modules.analysis.AsyncOpenAI') as mock_openai:
            
            # Setup mock database
            mock_db = Mock()
            mock_db.get_prospect_by_name = AsyncMock()
            mock_db.create_prospect = AsyncMock()
            mock_db.get_all_prospects = AsyncMock()
            mock_db.insert_reddit_urls = AsyncMock()
            mock_db.insert_posts_comments = AsyncMock()
            mock_db.insert_analysis_result = AsyncMock()
            
            mock_db_class.return_value = mock_db
            mock_db_class2.return_value = mock_db
            mock_db_class3.return_value = mock_db
            mock_db_class4.return_value = mock_db
            
            # Setup mock settings
            mock_settings.return_value.APIFY_API_KEY = "test-token"
            mock_settings.return_value.APIFY_ACTOR = "apify/google-search-scraper"
            mock_settings.return_value.MAX_REDDIT_URLS = 10
            
            mock_settings2.return_value.APIFY_API_KEY = "test-token"
            mock_settings2.return_value.APIFY_ACTOR = "trudax/reddit-scraper-lite"
            mock_settings2.return_value.MAX_POSTS_PER_URL = 20
            mock_settings2.return_value.MAX_COMMENTS_PER_POST = 20
            
            mock_settings3.return_value.OPENAI_API_KEY = "test-key"
            
            # Setup mock OpenAI
            mock_openai.return_value = Mock()
            
            yield mock_db
    
    @pytest.mark.asyncio
    async def test_complete_workflow_new_brand(self, mock_environment):
        """Test complete workflow for a new brand"""
        from modules.brand_selector import BrandSelector
        from modules.google_search import GoogleSearcher
        from modules.reddit_scraper import RedditScraper
        from modules.data_processor import DataProcessor
        from modules.analysis import Analyzer
        
        # Setup mock data
        prospect_data = {
            'id': 'test-prospect-123',
            'brand_name': 'Test Brand',
            'industry_category': 'Wellness'
        }
        
        reddit_urls = [
            'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
            'https://reddit.com/r/Wellness/comments/def456/test-brand-discussion'
        ]
        
        reddit_data = [
            {
                'post_id': 'post-1',
                'body': 'Test Brand is amazing! Great results.',
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T10:30:00Z',
                'up_votes': 10,
                'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
                'data_type': 'post'
            }
        ]
        
        analysis_result = {
            'brand_name': 'Test Brand',
            'key_insight': 'Test Brand faces a "social proof cascade failure"',
            'html_content': '<html><body>Analysis report</body></html>',
            'analysis_date': '2024-01-15T12:00:00Z',
            'prospect_id': 'test-prospect-123'
        }
        
        # Setup mocks
        mock_environment.get_prospect_by_name.return_value = None
        mock_environment.create_prospect.return_value = prospect_data
        mock_environment.insert_analysis_result.return_value = analysis_result
        
        # Mock user input for brand selector
        with patch('modules.brand_selector.Prompt') as mock_prompt:
            mock_prompt.ask.side_effect = [
                "San Francisco, CA",  # HQ Location
                "Wellness",           # Industry Category
                "$1M-$10M",          # Revenue Range
                "https://testbrand.com",  # Website
                "https://linkedin.com/company/testbrand",  # LinkedIn
                "DTC wellness brand in target range"  # Why good fit
            ]:
                
                # Step 1: Brand Selection
                brand_selector = BrandSelector()
                prospect = await brand_selector.get_or_create_prospect("Test Brand")
                
                assert prospect == prospect_data
                mock_environment.get_prospect_by_name.assert_called_with("Test Brand")
                mock_environment.create_prospect.assert_called_once()
        
        # Step 2: Google Search
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    'organicResults': [
                        {'url': url, 'title': f'Test Brand Discussion', 'snippet': 'Reddit discussion'}
                        for url in reddit_urls
                    ]
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            searcher = GoogleSearcher()
            found_urls = await searcher.search_reddit_urls("Test Brand", "Wellness")
            
            assert len(found_urls) == 2
            assert all('reddit.com' in url for url in found_urls)
        
        # Step 3: Reddit Scraping
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = reddit_data
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            scraper = RedditScraper()
            scraped_data = await scraper.scrape_all_urls(reddit_urls, "Test Brand", "test-prospect-123")
            
            assert len(scraped_data) == len(reddit_data) * len(reddit_urls)
            mock_environment.insert_posts_comments.assert_called()
        
        # Step 4: Data Processing
        processor = DataProcessor()
        cleaned_data = await processor.process_data(scraped_data, "Test Brand", "test-prospect-123")
        
        assert len(cleaned_data) > 0
        assert all(item['brandName'] == "Test Brand" for item in cleaned_data)
        assert all(item['prospect_id'] == "test-prospect-123" for item in cleaned_data)
        
        # Step 5: Analysis
        with patch('modules.analysis.AsyncOpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create = AsyncMock(return_value={
                'choices': [{'message': {'content': '''
<BRAND_NAME>Test Brand</BRAND_NAME>
<KEY_INSIGHT>Test Brand faces a "social proof cascade failure"</KEY_INSIGHT>
<HTML_REPORT><html><body>Analysis report</body></html></HTML_REPORT>
'''}}]
            })
            
            analyzer = Analyzer()
            result = await analyzer.analyze(cleaned_data, "Test Brand", "test-prospect-123")
            
            assert result['brand_name'] == "Test Brand"
            assert "social proof cascade failure" in result['key_insight']
            assert "<html>" in result['html_content']
            mock_environment.insert_analysis_result.assert_called()
    
    @pytest.mark.asyncio
    async def test_workflow_existing_brand(self, mock_environment):
        """Test workflow with existing brand"""
        from modules.brand_selector import BrandSelector
        
        # Setup existing prospect
        existing_prospect = {
            'id': 'existing-123',
            'brand_name': 'Existing Brand',
            'industry_category': 'Health'
        }
        
        mock_environment.get_prospect_by_name.return_value = existing_prospect
        
        # Execute
        brand_selector = BrandSelector()
        prospect = await brand_selector.get_or_create_prospect("Existing Brand")
        
        # Assert
        assert prospect == existing_prospect
        mock_environment.get_prospect_by_name.assert_called_with("Existing Brand")
        mock_environment.create_prospect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, mock_environment):
        """Test workflow error handling"""
        from modules.google_search import GoogleSearcher
        import httpx
        
        # Setup error in Google search
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock()
            )
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            searcher = GoogleSearcher()
            
            # Execute & Assert
            with pytest.raises(httpx.HTTPStatusError):
                await searcher.search_reddit_urls("Test Brand")
    
    @pytest.mark.asyncio
    async def test_workflow_no_reddit_urls_found(self, mock_environment):
        """Test workflow when no Reddit URLs are found"""
        from modules.google_search import GoogleSearcher
        
        # Setup empty search results
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [{'organicResults': []}]
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            searcher = GoogleSearcher()
            urls = await searcher.search_reddit_urls("Unknown Brand")
            
            assert urls == []
    
    @pytest.mark.asyncio
    async def test_workflow_data_processing_pipeline(self, mock_environment):
        """Test the data processing pipeline with various data types"""
        from modules.data_processor import DataProcessor
        
        # Setup mixed data (valid, spam, deleted, etc.)
        mixed_data = [
            {
                'post_id': 'post-1',
                'body': 'Test Brand is amazing! I love the results.',
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T10:30:00Z',
                'up_votes': 10,
                'url': 'https://reddit.com/r/test/comments/1',
                'data_type': 'post'
            },
            {
                'post_id': 'post-2',
                'body': '[deleted]',  # Should be filtered
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T11:00:00Z',
                'up_votes': 0,
                'url': 'https://reddit.com/r/test/comments/2',
                'data_type': 'post'
            },
            {
                'post_id': 'post-3',
                'body': 'I am a bot and this action was performed automatically.',  # Should be filtered
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T11:30:00Z',
                'up_votes': 0,
                'url': 'https://reddit.com/r/test/comments/3',
                'data_type': 'post'
            }
        ]
        
        processor = DataProcessor()
        result = await processor.process_data(mixed_data, "Test Brand", "test-prospect-123")
        
        # Should only have 1 valid item after filtering
        assert len(result) == 1
        assert result[0]['post_id'] == 'post-1'
        assert result[0]['brandName'] == "Test Brand"
        assert result[0]['prospect_id'] == "test-prospect-123"
