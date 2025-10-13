"""
Simple test script to test the workflow without database connections
"""

import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

async def test_workflow():
    """Test the workflow logic without database connections"""
    console.print("\n[bold cyan]🔍 Brand Reddit Analysis Tool - Test Mode[/bold cyan]\n")
    
    # Step 1: Brand Selection
    console.print("[yellow]Step 1: Brand Selection[/yellow]")
    
    run_all = Confirm.ask("Do you want to run analysis for all prospects?")
    
    if run_all:
        console.print("[green]✓ Would run analysis for all prospects[/green]")
        console.print("[cyan]Found 3 prospects to analyze:[/cyan]")
        console.print("  - Seed Health (Wellness)")
        console.print("  - Athletic Greens (Supplements)")
        console.print("  - Ritual (Vitamins)")
    else:
        brand_name = Prompt.ask("Enter brand name to analyze")
        console.print(f"[green]✓ Would analyze brand: {brand_name}[/green]")
        
        # Simulate prospect creation/selection
        console.print(f"[yellow]Creating new prospect: {brand_name}[/yellow]")
        console.print(f"[green]✓ Created new prospect with ID: test-prospect-123[/green]")
    
    # Step 2: Google Search
    console.print(f"\n[yellow]Step 2: Searching Reddit URLs[/yellow]")
    console.print(f"[green]✓ Found 5 Reddit URLs for {brand_name if not run_all else 'prospects'}:[/green]")
    console.print("  - https://reddit.com/r/Supplements/comments/abc123/brand-review")
    console.print("  - https://reddit.com/r/Wellness/comments/def456/brand-discussion")
    console.print("  - https://reddit.com/r/Health/comments/ghi789/brand-experience")
    console.print("  - https://reddit.com/r/Nootropics/comments/jkl012/brand-testimonial")
    console.print("  - https://reddit.com/r/Biohackers/comments/mno345/brand-results")
    
    # Step 3: Reddit Scraping
    console.print(f"\n[yellow]Step 3: Scraping Reddit posts & comments[/yellow]")
    console.print("[green]✓ Scraped 47 posts and 156 comments[/green]")
    
    # Step 4: Data Processing
    console.print(f"\n[yellow]Step 4: Processing and cleaning data[/yellow]")
    console.print("[green]✓ Cleaned data: 38 valid items (filtered out 9 bot/spam posts)[/green]")
    
    # Step 5: Analysis
    console.print(f"\n[yellow]Step 5: Running ChatGPT analysis[/yellow]")
    console.print("[green]✓ Analysis complete![/green]")
    console.print(f"[cyan]Key Insight:[/cyan] {brand_name if not run_all else 'Brand'} faces a 'social proof cascade failure' - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation")
    
    console.print(f"\n[bold green]🎉 Workflow test completed successfully![/bold green]")

if __name__ == "__main__":
    asyncio.run(test_workflow())

