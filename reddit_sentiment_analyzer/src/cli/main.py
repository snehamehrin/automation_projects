"""
Command-line interface for the Reddit Sentiment Analyzer.

This module provides CLI commands for running sentiment analysis from the
command line, including single brand analysis and batch processing.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ..core.analyzer import RedditSentimentAnalyzer
from ..data.models import BrandData, AnalysisResult
from ..utils.logging import get_logger, initialize_logging
from ..config.settings import get_settings

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, verbose, debug):
    """Reddit Sentiment Analyzer CLI."""
    # Initialize logging
    if debug:
        initialize_logging()
    
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug


@cli.command()
@click.option('--brand', '-b', required=True, help='Brand name to analyze')
@click.option('--category', '-c', help='Brand category/industry')
@click.option('--url', '-u', help='Company website URL')
@click.option('--output', '-o', help='Output file path (JSON)')
@click.option('--html', is_flag=True, help='Save HTML report')
@click.pass_context
def analyze_single(ctx, brand, category, url, output, html):
    """Analyze sentiment for a single brand."""
    asyncio.run(_analyze_single_brand(ctx, brand, category, url, output, html))


@cli.command()
@click.option('--sheet-id', '-s', required=True, help='Google Sheet ID')
@click.option('--output-sheet', '-o', help='Output Google Sheet ID')
@click.option('--output-file', '-f', help='Output file path (JSON)')
@click.pass_context
def analyze_sheets(ctx, sheet_id, output_sheet, output_file):
    """Analyze brands from a Google Sheet."""
    asyncio.run(_analyze_google_sheets(ctx, sheet_id, output_sheet, output_file))


@cli.command()
@click.option('--input-file', '-i', required=True, help='Input JSON file with brand data')
@click.option('--output-file', '-o', help='Output file path (JSON)')
@click.option('--output-sheet', '-s', help='Output Google Sheet ID')
@click.pass_context
def analyze_batch(ctx, input_file, output_file, output_sheet):
    """Analyze multiple brands from a JSON file."""
    asyncio.run(_analyze_batch_brands(ctx, input_file, output_file, output_sheet))


@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--max-results', '-m', default=50, help='Maximum results')
@click.option('--output', '-o', help='Output file path (JSON)')
@click.pass_context
def search(ctx, query, max_results, output):
    """Search for Reddit content."""
    asyncio.run(_search_reddit_content(ctx, query, max_results, output))


@cli.command()
def config():
    """Show current configuration."""
    _show_configuration()


@cli.command()
def health():
    """Check service health."""
    asyncio.run(_check_health())


async def _analyze_single_brand(ctx, brand, category, url, output, html):
    """Analyze a single brand."""
    console.print(f"[bold blue]Analyzing brand: {brand}[/bold blue]")
    
    try:
        # Create brand data
        brand_data = BrandData(
            name=brand,
            category=category,
            company_url=url
        )
        
        # Initialize analyzer
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing analyzer...", total=None)
            
            analyzer = RedditSentimentAnalyzer()
            await analyzer.initialize()
            
            progress.update(task, description="Analyzing brand...")
            
            # Perform analysis
            result = await analyzer.analyze_brand(brand_data)
            
            progress.update(task, description="Analysis complete!")
        
        # Display results
        _display_analysis_result(result)
        
        # Save results
        if output:
            _save_analysis_result(result, output)
        
        if html and result.html_report:
            html_file = output.replace('.json', '.html') if output else f"{brand}_report.html"
            _save_html_report(result.html_report, html_file)
        
        await analyzer.close()
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.error(f"Error in single brand analysis: {e}", exc_info=True)
        sys.exit(1)


async def _analyze_google_sheets(ctx, sheet_id, output_sheet, output_file):
    """Analyze brands from Google Sheets."""
    console.print(f"[bold blue]Analyzing brands from Google Sheet: {sheet_id}[/bold blue]")
    
    try:
        # Initialize analyzer
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing analyzer...", total=None)
            
            analyzer = RedditSentimentAnalyzer()
            await analyzer.initialize()
            
            progress.update(task, description="Loading brands from sheet...")
            
            # Perform analysis
            results = await analyzer.analyze_from_google_sheets(
                sheet_id=sheet_id,
                output_sheet_id=output_sheet
            )
            
            progress.update(task, description="Analysis complete!")
        
        # Display results
        _display_batch_results(results)
        
        # Save results
        if output_file:
            _save_batch_results(results, output_file)
        
        await analyzer.close()
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.error(f"Error in Google Sheets analysis: {e}", exc_info=True)
        sys.exit(1)


async def _analyze_batch_brands(ctx, input_file, output_file, output_sheet):
    """Analyze multiple brands from a JSON file."""
    console.print(f"[bold blue]Analyzing brands from file: {input_file}[/bold blue]")
    
    try:
        # Load brand data
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        brands = []
        if isinstance(data, list):
            brands = [BrandData(**brand) for brand in data]
        elif isinstance(data, dict) and 'brands' in data:
            brands = [BrandData(**brand) for brand in data['brands']]
        else:
            raise ValueError("Invalid JSON format. Expected list of brands or object with 'brands' key.")
        
        console.print(f"Loaded {len(brands)} brands")
        
        # Initialize analyzer
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing analyzer...", total=None)
            
            analyzer = RedditSentimentAnalyzer()
            await analyzer.initialize()
            
            progress.update(task, description="Analyzing brands...")
            
            # Perform batch analysis
            results = await analyzer.analyze_brands_batch(brands)
            
            progress.update(task, description="Analysis complete!")
        
        # Display results
        _display_batch_results(results)
        
        # Save results
        if output_file:
            _save_batch_results(results, output_file)
        
        # Save to Google Sheets if specified
        if output_sheet and results:
            console.print(f"Saving results to Google Sheet: {output_sheet}")
            await analyzer.google_sheets.save_analysis_results(output_sheet, results)
        
        await analyzer.close()
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.error(f"Error in batch analysis: {e}", exc_info=True)
        sys.exit(1)


async def _search_reddit_content(ctx, query, max_results, output):
    """Search for Reddit content."""
    console.print(f"[bold blue]Searching for: {query}[/bold blue]")
    
    try:
        # Initialize analyzer
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing analyzer...", total=None)
            
            analyzer = RedditSentimentAnalyzer()
            await analyzer.initialize()
            
            progress.update(task, description="Searching Reddit...")
            
            # Perform search
            reddit_urls = await analyzer._search_reddit_urls(query)
            
            progress.update(task, description="Search complete!")
        
        # Display results
        _display_search_results(query, reddit_urls)
        
        # Save results
        if output:
            _save_search_results(query, reddit_urls, output)
        
        await analyzer.close()
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.error(f"Error in Reddit search: {e}", exc_info=True)
        sys.exit(1)


def _show_configuration():
    """Show current configuration."""
    settings = get_settings()
    
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Environment", settings.environment)
    table.add_row("Debug", str(settings.debug))
    table.add_row("API Host", settings.api.host)
    table.add_row("API Port", str(settings.api.port))
    table.add_row("Database URL", settings.database.url.split('@')[-1] if '@' in settings.database.url else "Not configured")
    table.add_row("OpenAI API Key", "***" if settings.external_apis.openai_api_key else "Not set")
    table.add_row("Apify API Key", "***" if settings.external_apis.apify_api_key else "Not set")
    
    console.print(table)


async def _check_health():
    """Check service health."""
    console.print("[bold blue]Checking service health...[/bold blue]")
    
    try:
        # Initialize analyzer
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Test connections
        health_status = {
            "OpenAI": await analyzer.openai.test_connection(),
            "Apify": await analyzer.apify.test_connection(),
            "Google Sheets": await analyzer.google_sheets.test_connection("test")
        }
        
        # Display health status
        table = Table(title="Service Health")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        
        for service, status in health_status.items():
            status_text = "✅ Healthy" if status else "❌ Unhealthy"
            table.add_row(service, status_text)
        
        console.print(table)
        
        await analyzer.close()
        
    except Exception as e:
        console.print(f"[bold red]Health check failed: {e}[/bold red]")
        sys.exit(1)


def _display_analysis_result(result: AnalysisResult):
    """Display analysis result in a formatted table."""
    console.print(f"\n[bold green]Analysis Results for {result.brand_name}[/bold green]")
    
    # Key insight
    console.print(Panel(result.key_insight, title="Key Insight", border_style="green"))
    
    # Sentiment summary
    if result.sentiment_summary:
        table = Table(title="Sentiment Summary")
        table.add_column("Sentiment", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")
        
        total = result.sentiment_summary.get('total', 0)
        for sentiment in ['positive', 'negative', 'neutral']:
            count = result.sentiment_summary.get(sentiment, 0)
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(sentiment.title(), str(count), f"{percentage:.1f}%")
        
        console.print(table)
    
    # Thematic breakdown
    if result.thematic_breakdown:
        console.print("\n[bold]Thematic Breakdown:[/bold]")
        for i, theme in enumerate(result.thematic_breakdown, 1):
            console.print(f"  {i}. {theme}")
    
    # Strategic recommendations
    if result.strategic_recommendations:
        console.print("\n[bold]Strategic Recommendations:[/bold]")
        for i, rec in enumerate(result.strategic_recommendations, 1):
            console.print(f"  {i}. {rec}")


def _display_batch_results(results: List[AnalysisResult]):
    """Display batch analysis results."""
    console.print(f"\n[bold green]Batch Analysis Results ({len(results)} brands)[/bold green]")
    
    table = Table(title="Summary")
    table.add_column("Brand", style="cyan")
    table.add_column("Posts", style="green")
    table.add_column("Key Insight", style="yellow")
    
    for result in results:
        insight = result.key_insight[:50] + "..." if len(result.key_insight) > 50 else result.key_insight
        table.add_row(result.brand_name, str(result.total_posts), insight)
    
    console.print(table)


def _display_search_results(query: str, urls: List[str]):
    """Display search results."""
    console.print(f"\n[bold green]Search Results for: {query}[/bold green]")
    console.print(f"Found {len(urls)} Reddit URLs")
    
    for i, url in enumerate(urls[:10], 1):  # Show first 10
        console.print(f"  {i}. {url}")
    
    if len(urls) > 10:
        console.print(f"  ... and {len(urls) - 10} more")


def _save_analysis_result(result: AnalysisResult, file_path: str):
    """Save analysis result to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(result.dict(), f, indent=2, default=str)
    
    console.print(f"[green]Results saved to: {file_path}[/green]")


def _save_batch_results(results: List[AnalysisResult], file_path: str):
    """Save batch results to JSON file."""
    data = [result.dict() for result in results]
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    console.print(f"[green]Results saved to: {file_path}[/green]")


def _save_html_report(html_content: str, file_path: str):
    """Save HTML report to file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    console.print(f"[green]HTML report saved to: {file_path}[/green]")


def _save_search_results(query: str, urls: List[str], file_path: str):
    """Save search results to JSON file."""
    data = {
        "query": query,
        "urls": urls,
        "count": len(urls)
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    console.print(f"[green]Search results saved to: {file_path}[/green]")


if __name__ == "__main__":
    cli()
