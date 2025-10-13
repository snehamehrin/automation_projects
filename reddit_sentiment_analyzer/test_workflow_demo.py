"""
Demo script to show the workflow without requiring user input
"""

import asyncio
from rich.console import Console

console = Console()

async def demo_workflow():
    """Demo the workflow with simulated user choices"""
    console.print("\n[bold cyan]🔍 Brand Reddit Analysis Tool - Demo Mode[/bold cyan]\n")
    
    # Simulate user choosing to enter a new brand
    console.print("[yellow]Step 1: Brand Selection[/yellow]")
    console.print("User choice: Enter a new brand name")
    brand_name = "Seed Health"
    console.print(f"[green]✓ Analyzing brand: {brand_name}[/green]")
    
    # Simulate prospect creation
    console.print(f"[yellow]Creating new prospect: {brand_name}[/yellow]")
    console.print(f"[green]✓ Created new prospect with ID: test-prospect-123[/green]")
    
    # Step 2: Google Search
    console.print(f"\n[yellow]Step 2: Searching Reddit URLs for {brand_name}[/yellow]")
    console.print(f"[green]✓ Found 5 Reddit URLs:[/green]")
    console.print("  - https://reddit.com/r/Supplements/comments/abc123/seed-health-review")
    console.print("  - https://reddit.com/r/Wellness/comments/def456/seed-health-discussion")
    console.print("  - https://reddit.com/r/Health/comments/ghi789/seed-health-experience")
    console.print("  - https://reddit.com/r/Nootropics/comments/jkl012/seed-health-testimonial")
    console.print("  - https://reddit.com/r/Biohackers/comments/mno345/seed-health-results")
    
    # Step 3: Reddit Scraping
    console.print(f"\n[yellow]Step 3: Scraping Reddit posts & comments[/yellow]")
    console.print("[green]✓ Scraped 47 posts and 156 comments[/green]")
    
    # Step 4: Data Processing
    console.print(f"\n[yellow]Step 4: Processing and cleaning data[/yellow]")
    console.print("[green]✓ Cleaned data: 38 valid items (filtered out 9 bot/spam posts)[/green]")
    
    # Step 5: Analysis
    console.print(f"\n[yellow]Step 5: Running ChatGPT analysis[/yellow]")
    console.print("[green]✓ Analysis complete![/green]")
    console.print(f"[cyan]Key Insight:[/cyan] {brand_name} faces a 'social proof cascade failure' - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation")
    
    console.print(f"\n[bold green]🎉 Workflow demo completed successfully![/bold green]")
    console.print("\n[dim]Note: This was a demo. The actual workflow would:")
    console.print("[dim]  - Connect to your Supabase database")
    console.print("[dim]  - Use real Apify APIs for Google search and Reddit scraping")
    console.print("[dim]  - Use OpenAI API for analysis")
    console.print("[dim]  - Save results to your database[/dim]")

if __name__ == "__main__":
    asyncio.run(demo_workflow())
