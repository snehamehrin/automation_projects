"""
Test the workflow with REAL API calls and REAL database operations
"""

import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

async def test_real_workflow():
    """Test the complete workflow with real APIs and database"""
    console.print("\n[bold cyan]🔍 Brand Reddit Analysis Tool - REAL Test[/bold cyan]\n")
    
    # Import modules
    from modules.brand_selector import BrandSelector
    from modules.google_search import GoogleSearcher
    from modules.reddit_scraper import RedditScraper
    from modules.data_processor import DataProcessor
    from modules.analysis import Analyzer
    
    # Step 1: Brand Selection
    console.print("[yellow]Step 1: Brand Selection[/yellow]")
    brand_selector = BrandSelector()
    
    # Ask user for real input
    run_all = Confirm.ask("Do you want to run analysis for all prospects?")
    
    if run_all:
        prospects = await brand_selector.get_all_prospects()
        console.print(f"[green]Found {len(prospects)} prospects to analyze[/green]")
        for prospect in prospects:
            console.print(f"  - {prospect['brand_name']} ({prospect.get('industry_category', 'N/A')})")
    else:
        brand_name = Prompt.ask("Enter brand name to analyze")
        prospect = await brand_selector.get_or_create_prospect(brand_name)
        prospects = [prospect]
        console.print(f"[green]✓ Working with prospect: {prospect['brand_name']} (ID: {prospect['id']})[/green]")
    
    # Process each prospect
    for prospect in prospects:
        await process_real_prospect(prospect)

async def process_real_prospect(prospect):
    """Process a single prospect with real APIs"""
    brand_name = prospect['brand_name']
    prospect_id = prospect['id']
    
    console.print(f"\n[bold blue]Processing: {brand_name}[/bold blue]")
    
    try:
        # Step 2: Google Search for Reddit URLs
        console.print(f"[yellow]Step 2: Searching Reddit URLs for {brand_name}[/yellow]")
        searcher = GoogleSearcher()
        reddit_urls = await searcher.search_reddit_urls(brand_name, prospect.get('industry_category', ''))
        
        if not reddit_urls:
            console.print(f"[red]No Reddit URLs found for {brand_name}[/red]")
            return
        
        console.print(f"[green]Found {len(reddit_urls)} Reddit URLs[/green]")
        for url in reddit_urls:
            console.print(f"  - {url}")
        
        # Step 3: Update prospect with URLs
        await searcher.update_prospect_urls(prospect_id, reddit_urls)
        console.print(f"[green]✓ Stored URLs in database[/green]")
        
        # Step 4: Scrape Reddit Posts & Comments
        console.print(f"[yellow]Step 3: Scraping Reddit posts & comments[/yellow]")
        scraper = RedditScraper()
        posts_comments = await scraper.scrape_all_urls(reddit_urls, brand_name, prospect_id)
        
        if not posts_comments:
            console.print(f"[red]No Reddit data scraped for {brand_name}[/red]")
            return
        
        console.print(f"[green]Scraped {len(posts_comments)} posts/comments[/green]")
        posts_count = len([p for p in posts_comments if p['data_type'] == 'post'])
        comments_count = len([p for p in posts_comments if p['data_type'] == 'comment'])
        console.print(f"  - Posts: {posts_count}")
        console.print(f"  - Comments: {comments_count}")
        
        # Step 5: Process & Clean Data
        console.print(f"[yellow]Step 4: Processing and cleaning data[/yellow]")
        processor = DataProcessor()
        cleaned_data = await processor.process_data(posts_comments, brand_name, prospect_id)
        
        console.print(f"[green]Cleaned data: {len(cleaned_data)} valid items[/green]")
        
        if not cleaned_data:
            console.print(f"[red]No valid data after cleaning for {brand_name}[/red]")
            return
        
        # Step 6: Run Analysis
        console.print(f"[yellow]Step 5: Running ChatGPT analysis[/yellow]")
        analyzer = Analyzer()
        analysis_result = await analyzer.analyze(cleaned_data, brand_name, prospect_id)
        
        console.print(f"[bold green]✓ Analysis complete for {brand_name}![/bold green]")
        console.print(f"[cyan]Key Insight:[/cyan] {analysis_result['key_insight']}")
        console.print(f"[cyan]HTML Report:[/cyan] {len(analysis_result['html_content'])} characters")
        console.print(f"[cyan]Analysis Date:[/cyan] {analysis_result['analysis_date']}")
        
    except Exception as e:
        console.print(f"[red]Error processing {brand_name}: {str(e)}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    asyncio.run(test_real_workflow())

