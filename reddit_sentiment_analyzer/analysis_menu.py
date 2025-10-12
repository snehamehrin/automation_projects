#!/usr/bin/env python3
"""
Interactive analysis menu for Reddit Sentiment Analyzer.

This script provides a menu to choose between:
1. Single brand analysis (manual input)
2. Multiple brand analysis (from Supabase)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData
from src.utils.logging import get_logger, initialize_logging

logger = get_logger(__name__)


def display_menu():
    """Display the main menu."""
    print("\n" + "=" * 60)
    print("🚀 Reddit Sentiment Analyzer")
    print("=" * 60)
    print("Choose your analysis type:")
    print()
    print("1. 📝 Single Brand Analysis")
    print("   - Enter brand details manually")
    print("   - Perfect for testing or one-off analysis")
    print()
    print("2. 📊 Multiple Brand Analysis")
    print("   - Load brands from Supabase database")
    print("   - Analyze all prospects in your database")
    print()
    print("3. 🔍 View Prospects in Database")
    print("   - See what brands are available in Supabase")
    print()
    print("0. ❌ Exit")
    print("=" * 60)


def get_brand_input():
    """Get brand details from user input."""
    print("\n📝 Single Brand Analysis")
    print("-" * 30)
    
    # Get brand name (required)
    while True:
        brand_name = input("Brand Name: ").strip()
        if brand_name:
            break
        print("❌ Brand name is required!")
    
    # Get category (optional)
    category = input("Category (optional, e.g., Technology, Fashion): ").strip()
    if not category:
        category = None
    
    # Get company URL (optional)
    company_url = input("Company URL (optional, e.g., https://example.com): ").strip()
    if not company_url:
        company_url = None
    elif not company_url.startswith(('http://', 'https://')):
        company_url = f"https://{company_url}"
    
    return BrandData(
        name=brand_name,
        category=category,
        company_url=company_url
    )


async def single_brand_analysis():
    """Perform single brand analysis."""
    print("\n🎯 Single Brand Analysis")
    print("=" * 40)
    
    try:
        # Get brand details from user
        brand_data = get_brand_input()
        
        print(f"\n📋 Brand Details:")
        print(f"   Name: {brand_data.name}")
        print(f"   Category: {brand_data.category or 'Not specified'}")
        print(f"   URL: {brand_data.company_url or 'Not specified'}")
        
        # Confirm before proceeding
        confirm = input("\n🤔 Proceed with analysis? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Analysis cancelled.")
            return False
        
        # Initialize analyzer
        print("\n🔄 Initializing analyzer...")
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Perform analysis
        print(f"\n🔍 Analyzing {brand_data.name}...")
        print("   This may take a few minutes...")
        
        result = await analyzer.analyze_brand(brand_data)
        
        # Display results
        print(f"\n📊 Analysis Results for {result.brand_name}")
        print("=" * 50)
        print(f"📈 Total Posts Analyzed: {result.total_posts}")
        print(f"💡 Key Insight: {result.key_insight}")
        
        if result.sentiment_summary:
            print(f"\n📊 Sentiment Summary:")
            for sentiment, value in result.sentiment_summary.items():
                print(f"   {sentiment.capitalize()}: {value}")
        
        if result.thematic_breakdown:
            print(f"\n🎯 Thematic Breakdown:")
            for i, theme in enumerate(result.thematic_breakdown[:5], 1):
                print(f"   {i}. {theme}")
        
        if result.strategic_recommendations:
            print(f"\n💼 Strategic Recommendations:")
            for i, rec in enumerate(result.strategic_recommendations[:3], 1):
                print(f"   {i}. {rec}")
        
        # Save HTML report
        if result.html_report:
            report_file = f"report_{brand_data.name.lower().replace(' ', '_')}.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(result.html_report)
            print(f"\n📄 HTML report saved to: {report_file}")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        logger.error(f"Single brand analysis error: {e}", exc_info=True)
        return False


async def multiple_brand_analysis():
    """Perform multiple brand analysis from Supabase."""
    print("\n📊 Multiple Brand Analysis")
    print("=" * 40)
    
    try:
        # Initialize analyzer
        print("🔄 Initializing analyzer...")
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Load brands from Supabase
        print("📖 Loading brands from Supabase...")
        brands = await analyzer.supabase.load_brands()
        
        if not brands:
            print("❌ No brands found in Supabase database!")
            print("   Please add some brands to your 'prospects' table first.")
            await analyzer.close()
            return False
        
        print(f"📋 Found {len(brands)} brands to analyze:")
        for i, brand in enumerate(brands, 1):
            print(f"   {i}. {brand.name} ({brand.category or 'No category'})")
        
        # Confirm before proceeding
        print(f"\n⚠️  This will analyze {len(brands)} brands and may take a while.")
        confirm = input("🤔 Proceed with batch analysis? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Analysis cancelled.")
            await analyzer.close()
            return False
        
        # Perform batch analysis
        print(f"\n🔍 Starting batch analysis of {len(brands)} brands...")
        print("   This may take several minutes...")
        
        results = await analyzer.analyze_brands_batch(brands)
        
        # Display results summary
        print(f"\n📊 Batch Analysis Results")
        print("=" * 50)
        print(f"✅ Successfully analyzed: {len(results)} brands")
        print(f"❌ Failed analyses: {len(brands) - len(results)} brands")
        
        if results:
            print(f"\n📋 Analysis Summary:")
            for result in results:
                print(f"   • {result.brand_name}: {result.total_posts} posts, Key insight: {result.key_insight[:50]}...")
        
        # Results are automatically saved to Supabase
        print(f"\n💾 Results have been saved to Supabase 'analysis_results' table")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Batch analysis failed: {e}")
        logger.error(f"Multiple brand analysis error: {e}", exc_info=True)
        return False


async def view_prospects():
    """View prospects in the database."""
    print("\n🔍 Viewing Prospects in Database")
    print("=" * 40)
    
    try:
        # Initialize analyzer
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Load brands from Supabase
        print("📖 Loading prospects from Supabase...")
        brands = await analyzer.supabase.load_brands()
        
        if not brands:
            print("❌ No prospects found in database!")
            print("   The 'prospects' table is empty.")
            print("   Add some prospects to your Supabase database first.")
        else:
            print(f"📊 Found {len(brands)} prospects in database:")
            print()
            for i, brand in enumerate(brands, 1):
                print(f"   {i}. {brand.name}")
                if brand.category:
                    print(f"      Category: {brand.category}")
                if brand.company_url:
                    print(f"      URL: {brand.company_url}")
                print()
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to load prospects: {e}")
        logger.error(f"View prospects error: {e}", exc_info=True)
        return False


async def main():
    """Main menu loop."""
    # Initialize logging
    initialize_logging()
    
    while True:
        display_menu()
        
        try:
            choice = input("\nEnter your choice (0-3): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice == "1":
                await single_brand_analysis()
            elif choice == "2":
                await multiple_brand_analysis()
            elif choice == "3":
                await view_prospects()
            else:
                print("❌ Invalid choice. Please enter 0, 1, 2, or 3.")
            
            # Pause before showing menu again
            if choice in ["1", "2", "3"]:
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    asyncio.run(main())
