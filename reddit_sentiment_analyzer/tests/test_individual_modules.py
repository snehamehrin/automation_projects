"""
Individual module test scripts
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_brand_selector():
    """Test brand selector module"""
    print("🧪 Testing Brand Selector Module")
    print("=" * 40)
    
    try:
        from modules.brand_selector import BrandSelector
        
        # Test with mocked database
        with patch('modules.brand_selector.Database') as mock_db_class:
            mock_db = Mock()
            mock_db.get_prospect_by_name = AsyncMock(return_value=None)
            mock_db.create_prospect = AsyncMock(return_value={
                'id': 'test-123',
                'brand_name': 'Test Brand',
                'industry_category': 'Wellness'
            })
            mock_db_class.return_value = mock_db
            
            selector = BrandSelector()
            
            # Mock user input
            with patch('modules.brand_selector.Prompt') as mock_prompt:
                mock_prompt.ask.side_effect = [
                    "San Francisco, CA",
                    "Wellness", 
                    "$1M-$10M",
                    "https://testbrand.com",
                    "https://linkedin.com/company/testbrand",
                    "DTC wellness brand"
                ]
                
                prospect = await selector.get_or_create_prospect("Test Brand")
                print(f"✅ Created prospect: {prospect['brand_name']}")
                
    except Exception as e:
        print(f"❌ Brand Selector test failed: {e}")


async def test_google_search():
    """Test Google search module"""
    print("\n🧪 Testing Google Search Module")
    print("=" * 40)
    
    try:
        from modules.google_search import GoogleSearcher
        
        with patch('modules.google_search.Database') as mock_db_class, \
             patch('modules.google_search.get_settings') as mock_settings:
            
            mock_db = Mock()
            mock_db.insert_reddit_urls = AsyncMock()
            mock_db_class.return_value = mock_db
            
            mock_settings.return_value.APIFY_API_KEY = "test-token"
            mock_settings.return_value.APIFY_ACTOR = "apify/google-search-scraper"
            mock_settings.return_value.MAX_REDDIT_URLS = 10
            
            searcher = GoogleSearcher()
            
            # Mock HTTP response
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = [
                    {
                        'organicResults': [
                            {
                                'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand',
                                'title': 'Test Brand Review',
                                'snippet': 'Reddit discussion about Test Brand'
                            }
                        ]
                    }
                ]
                mock_response.raise_for_status.return_value = None
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                urls = await searcher.search_reddit_urls("Test Brand", "Wellness")
                print(f"✅ Found {len(urls)} Reddit URLs")
                
    except Exception as e:
        print(f"❌ Google Search test failed: {e}")


async def test_reddit_scraper():
    """Test Reddit scraper module"""
    print("\n🧪 Testing Reddit Scraper Module")
    print("=" * 40)
    
    try:
        from modules.reddit_scraper import RedditScraper
        
        with patch('modules.reddit_scraper.Database') as mock_db_class, \
             patch('modules.reddit_scraper.get_settings') as mock_settings:
            
            mock_db = Mock()
            mock_db.insert_posts_comments = AsyncMock()
            mock_db_class.return_value = mock_db
            
            mock_settings.return_value.APIFY_API_KEY = "test-token"
            mock_settings.return_value.APIFY_ACTOR = "trudax/reddit-scraper-lite"
            mock_settings.return_value.MAX_POSTS_PER_URL = 20
            mock_settings.return_value.MAX_COMMENTS_PER_POST = 20
            
            scraper = RedditScraper()
            
            # Mock HTTP response
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = [
                    {
                        'id': 'post-123',
                        'dataType': 'post',
                        'title': 'Test Brand Review',
                        'body': 'Great product!',
                        'url': 'https://reddit.com/r/test/comments/123',
                        'communityName': 'test',
                        'createdAt': '2024-01-15T10:30:00Z',
                        'upVotes': 10,
                        'commentsCount': 5
                    }
                ]
                mock_response.raise_for_status.return_value = None
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                urls = ['https://reddit.com/r/test/comments/123']
                data = await scraper.scrape_all_urls(urls, "Test Brand", "test-prospect-123")
                print(f"✅ Scraped {len(data)} posts/comments")
                
    except Exception as e:
        print(f"❌ Reddit Scraper test failed: {e}")


async def test_data_processor():
    """Test data processor module"""
    print("\n🧪 Testing Data Processor Module")
    print("=" * 40)
    
    try:
        from modules.data_processor import DataProcessor
        
        processor = DataProcessor()
        
        # Test data
        test_data = [
            {
                'post_id': 'post-1',
                'body': 'Test Brand is amazing! Great results.',
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
            }
        ]
        
        result = await processor.process_data(test_data, "Test Brand", "test-prospect-123")
        print(f"✅ Processed {len(result)} valid items from {len(test_data)} total")
        
    except Exception as e:
        print(f"❌ Data Processor test failed: {e}")


async def test_analysis():
    """Test analysis module"""
    print("\n🧪 Testing Analysis Module")
    print("=" * 40)
    
    try:
        from modules.analysis import Analyzer
        
        with patch('modules.analysis.Database') as mock_db_class, \
             patch('modules.analysis.get_settings') as mock_settings, \
             patch('modules.analysis.AsyncOpenAI') as mock_openai:
            
            mock_db = Mock()
            mock_db.insert_analysis_result = AsyncMock()
            mock_db_class.return_value = mock_db
            
            mock_settings.return_value.OPENAI_API_KEY = "test-key"
            
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value={
                'choices': [{'message': {'content': '''
<BRAND_NAME>Test Brand</BRAND_NAME>
<KEY_INSIGHT>Test Brand faces a "social proof cascade failure"</KEY_INSIGHT>
<HTML_REPORT><html><body>Analysis report</body></html></HTML_REPORT>
'''}}]
            })
            mock_openai.return_value = mock_client
            
            analyzer = Analyzer()
            
            # Test data
            test_posts = [
                {
                    'id': 'post-1',
                    'text': 'Test Brand is amazing!',
                    'subreddit': 'Supplements',
                    'createdAt': '2024-01-15T10:30:00Z',
                    'upVotes': 10,
                    'url': 'https://reddit.com/r/test/comments/1',
                    'brandName': 'Test Brand',
                    'prospect_id': 'test-prospect-123'
                }
            ]
            
            result = await analyzer.analyze(test_posts, "Test Brand", "test-prospect-123")
            print(f"✅ Generated analysis for {result['brand_name']}")
            print(f"   Key Insight: {result['key_insight'][:50]}...")
            
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")


async def test_database():
    """Test database module"""
    print("\n🧪 Testing Database Module")
    print("=" * 40)
    
    try:
        from database.db import Database
        
        with patch('database.db.create_client') as mock_create_client, \
             patch('database.db.get_settings') as mock_settings:
            
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [{'id': '123', 'brand_name': 'Test Brand'}]
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_create_client.return_value = mock_client
            
            mock_settings.return_value.SUPABASE_URL = "test-url"
            mock_settings.return_value.SUPABASE_KEY = "test-key"
            
            db = Database()
            prospect = await db.get_prospect_by_name("Test Brand")
            print(f"✅ Retrieved prospect: {prospect['brand_name']}")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")


async def run_all_module_tests():
    """Run all individual module tests"""
    print("🚀 Running All Module Tests")
    print("=" * 50)
    
    await test_brand_selector()
    await test_google_search()
    await test_reddit_scraper()
    await test_data_processor()
    await test_analysis()
    await test_database()
    
    print("\n" + "=" * 50)
    print("✅ All module tests completed!")


if __name__ == "__main__":
    # Import required modules
    from unittest.mock import Mock, patch, AsyncMock
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        if test_name == "brand_selector":
            asyncio.run(test_brand_selector())
        elif test_name == "google_search":
            asyncio.run(test_google_search())
        elif test_name == "reddit_scraper":
            asyncio.run(test_reddit_scraper())
        elif test_name == "data_processor":
            asyncio.run(test_data_processor())
        elif test_name == "analysis":
            asyncio.run(test_analysis())
        elif test_name == "database":
            asyncio.run(test_database())
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: brand_selector, google_search, reddit_scraper, data_processor, analysis, database")
    else:
        asyncio.run(run_all_module_tests())
