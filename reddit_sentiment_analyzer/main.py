"""
Brand Reddit Analysis - Main Workflow
Orchestrates the complete brand analysis pipeline
"""

import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm
from modules.brand_selector import BrandSelector
from modules.google_search import GoogleSearcher
from modules.reddit_scraper import RedditScraper
from modules.data_processor import DataProcessor
from modules.analysis import Analyzer
from utils.logger import setup_logger

console = Console()
logger = setup_logger()


async def main():
    """Main workflow orchestrator"""
    console.print("\n[bold cyan]🔍 Brand Reddit Analysis Tool[/bold cyan]\n")
    
    # Step 1: Brand Selection
    console.print("[yellow]Step 1: Brand Selection[/yellow]")
    brand_selector = BrandSelector()
    
    run_all = Confirm.ask("Do you want to run analysis for all prospects?")
    
    if run_all:
        prospects = await brand_selector.get_all_prospects()
        console.print(f"[green]Found {len(prospects)} prospects to analyze[/green]")
    else:
        brand_name = Prompt.ask("Enter brand name to analyze")
        prospect = await brand_selector.get_or_create_prospect(brand_name)
        prospects = [prospect]
    
    # Process each prospect
    for prospect in prospects:
        await process_prospect(prospect)


async def process_prospect(prospect: dict):
    """Process a single prospect through the entire pipeline"""
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
        
        # Step 3: Update prospect with URLs
        await searcher.update_prospect_urls(prospect_id, reddit_urls, brand_name)
        
        # Step 4: Scrape Reddit Posts & Comments
        console.print(f"[yellow]Step 3: Scraping Reddit posts & comments[/yellow]")
        scraper = RedditScraper()
        posts_comments = await scraper.scrape_all_urls(reddit_urls, brand_name, prospect_id)
        
        console.print(f"[green]Scraped {len(posts_comments)} posts/comments[/green]")
        
        # Step 5: Process & Clean Data
        console.print(f"[yellow]Step 4: Processing and cleaning data[/yellow]")
        processor = DataProcessor()
        cleaned_data = await processor.process_data(posts_comments, brand_name, prospect_id)
        
        console.print(f"[green]Cleaned data: {len(cleaned_data)} valid items[/green]")
        
        # Step 6: Run Analysis
        console.print(f"[yellow]Step 5: Running ChatGPT analysis[/yellow]")
        analyzer = Analyzer()
        analysis_result = await analyzer.analyze(cleaned_data, brand_name, prospect_id)
        
        console.print(f"[bold green]✓ Analysis complete for {brand_name}![/bold green]")
        console.print(f"[cyan]Key Insight:[/cyan] {analysis_result['key_insight'][:200]}...")
        
    except Exception as e:
        logger.error(f"Error processing {brand_name}: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    asyncio.run(main())

