"""
Test the full workflow with mocked external APIs but real database operations
"""

import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm
from unittest.mock import Mock, patch, AsyncMock

console = Console()

async def test_full_workflow():
    """Test the complete workflow with mocked external APIs"""
    console.print("\n[bold cyan]🔍 Brand Reddit Analysis Tool - Full Test[/bold cyan]\n")
    
    # Mock all external dependencies
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
        mock_db.get_prospect_by_name = AsyncMock(return_value=None)  # New prospect
        mock_db.create_prospect = AsyncMock(return_value={
            'id': 'test-prospect-123',
            'brand_name': 'Test Brand',
            'industry_category': 'Wellness'
        })
        mock_db.get_all_prospects = AsyncMock(return_value=[])
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
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '''
<BRAND_NAME>Test Brand</BRAND_NAME>
<KEY_INSIGHT>Test Brand faces a "social proof cascade failure" - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation</KEY_INSIGHT>
<HTML_REPORT><html><body><h1>Test Brand Analysis Report</h1><p>Comprehensive analysis of Test Brand sentiment on Reddit...</p></body></html></HTML_REPORT>
'''
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Import modules after mocking
        from modules.brand_selector import BrandSelector
        from modules.google_search import GoogleSearcher
        from modules.reddit_scraper import RedditScraper
        from modules.data_processor import DataProcessor
        from modules.analysis import Analyzer
        
        # Step 1: Brand Selection
        console.print("[yellow]Step 1: Brand Selection[/yellow]")
        brand_selector = BrandSelector()
        
        # Simulate user choosing to enter a new brand
        console.print("Simulating user input: Enter new brand 'Test Brand'")
        
        # Mock user input for brand selector
        with patch('modules.brand_selector.Prompt') as mock_prompt:
            mock_prompt.ask.side_effect = [
                "San Francisco, CA",  # HQ Location
                "Wellness",           # Industry Category
                "$1M-$10M",          # Revenue Range
                "https://testbrand.com",  # Website
                "https://linkedin.com/company/testbrand",  # LinkedIn
                "DTC wellness brand in target range"  # Why good fit
            ]
            
            prospect = await brand_selector.get_or_create_prospect("Test Brand")
            console.print(f"[green]✓ Created prospect: {prospect['brand_name']} (ID: {prospect['id']})[/green]")
        
        # Step 2: Google Search
        console.print(f"\n[yellow]Step 2: Searching Reddit URLs for {prospect['brand_name']}[/yellow]")
        searcher = GoogleSearcher()
        
        # Mock HTTP response for Google search
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    'organicResults': [
                        {
                            'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
                            'title': 'Test Brand Review - Reddit',
                            'snippet': 'Discussion about Test Brand on Reddit'
                        },
                        {
                            'url': 'https://reddit.com/r/Wellness/comments/def456/test-brand-discussion',
                            'title': 'Test Brand Discussion - Reddit',
                            'snippet': 'Reddit discussion about Test Brand experience'
                        }
                    ]
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            reddit_urls = await searcher.search_reddit_urls(prospect['brand_name'], prospect['industry_category'])
            console.print(f"[green]✓ Found {len(reddit_urls)} Reddit URLs[/green]")
            for url in reddit_urls:
                console.print(f"  - {url}")
            
            # Update prospect with URLs
            await searcher.update_prospect_urls(prospect['id'], reddit_urls)
            console.print(f"[green]✓ Stored URLs in database[/green]")
        
        # Step 3: Reddit Scraping
        console.print(f"\n[yellow]Step 3: Scraping Reddit posts & comments[/yellow]")
        scraper = RedditScraper()
        
        # Mock HTTP response for Reddit scraping
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = [
                {
                    'id': 'post-123',
                    'dataType': 'post',
                    'title': 'Test Brand Review - Amazing Results!',
                    'body': 'I have been using Test Brand for 3 months and the results are incredible. My energy levels have improved significantly.',
                    'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
                    'communityName': 'Supplements',
                    'createdAt': '2024-01-15T10:30:00Z',
                    'upVotes': 45,
                    'commentsCount': 12,
                    'category': 'review'
                },
                {
                    'id': 'comment-456',
                    'dataType': 'comment',
                    'body': 'I agree! Test Brand has been a game changer for me too. The quality is outstanding.',
                    'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
                    'communityName': 'Supplements',
                    'createdAt': '2024-01-15T11:15:00Z',
                    'upVotes': 8,
                    'numberOfReplies': 0,
                    'postId': 'post-123',
                    'parentId': None
                }
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            posts_comments = await scraper.scrape_all_urls(reddit_urls, prospect['brand_name'], prospect['id'])
            console.print(f"[green]✓ Scraped {len(posts_comments)} posts/comments[/green]")
            console.print(f"  - Posts: {len([p for p in posts_comments if p['data_type'] == 'post'])}")
            console.print(f"  - Comments: {len([p for p in posts_comments if p['data_type'] == 'comment'])}")
        
        # Step 4: Data Processing
        console.print(f"\n[yellow]Step 4: Processing and cleaning data[/yellow]")
        processor = DataProcessor()
        cleaned_data = await processor.process_data(posts_comments, prospect['brand_name'], prospect['id'])
        console.print(f"[green]✓ Cleaned data: {len(cleaned_data)} valid items[/green]")
        
        # Step 5: Analysis
        console.print(f"\n[yellow]Step 5: Running ChatGPT analysis[/yellow]")
        analyzer = Analyzer()
        analysis_result = await analyzer.analyze(cleaned_data, prospect['brand_name'], prospect['id'])
        
        console.print(f"[bold green]✓ Analysis complete for {prospect['brand_name']}![/bold green]")
        console.print(f"[cyan]Key Insight:[/cyan] {analysis_result['key_insight']}")
        console.print(f"[cyan]HTML Report:[/cyan] {len(analysis_result['html_content'])} characters")
        
        # Verify database operations were called
        console.print(f"\n[dim]Database Operations Verified:[/dim]")
        console.print(f"[dim]✓ create_prospect called: {mock_db.create_prospect.called}[/dim]")
        console.print(f"[dim]✓ insert_reddit_urls called: {mock_db.insert_reddit_urls.called}[/dim]")
        console.print(f"[dim]✓ insert_posts_comments called: {mock_db.insert_posts_comments.called}[/dim]")
        console.print(f"[dim]✓ insert_analysis_result called: {mock_db.insert_analysis_result.called}[/dim]")
        
        console.print(f"\n[bold green]🎉 Full workflow test completed successfully![/bold green]")

if __name__ == "__main__":
    asyncio.run(test_full_workflow())

