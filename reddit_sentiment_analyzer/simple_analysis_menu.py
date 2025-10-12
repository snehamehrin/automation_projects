#!/usr/bin/env python3
"""
Simple interactive analysis menu for Reddit Sentiment Analyzer.

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

from supabase import create_client, Client
from reddit_analyzer import RedditAnalyzer


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
    """Get brand name from user input."""
    print("\n📝 Single Brand Analysis")
    print("-" * 30)
    
    # Get brand name (required)
    while True:
        brand_name = input("Brand Name: ").strip()
        if brand_name:
            break
        print("❌ Brand name is required!")
    
    return {
        'name': brand_name,
        'category': None,
        'company_url': None
    }


def get_supabase_client():
    """Get Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials!")
        print("Please check your .env file has:")
        print("- SUPABASE_URL")
        print("- SUPABASE_KEY")
        return None
    
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None


async def single_brand_analysis():
    """Perform single brand analysis."""
    print("\n🎯 Single Brand Analysis")
    print("=" * 40)
    
    try:
        # Get brand details from user
        brand_data = get_brand_input()
        
        print(f"\n📋 Brand Details:")
        print(f"   Name: {brand_data['name']}")
        
        # Confirm before proceeding
        confirm = input("\n🤔 Proceed with analysis? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Analysis cancelled.")
            return False
        
        # Perform real analysis
        print(f"\n🔍 Analyzing {brand_data['name']}...")
        print("   This will:")
        print("   1. Search for Reddit posts about the brand")
        print("   2. Analyze sentiment using AI")
        print("   3. Generate insights and recommendations")
        print("   4. Create an HTML report")
        
        try:
            # Initialize analyzer
            analyzer = RedditAnalyzer()
            
            # Perform analysis
            result = await analyzer.analyze_brand(brand_data['name'])
            
            # Display results
            print(f"\n📊 Analysis Results for {result['brand_name']}")
            print("=" * 50)
            print(f"📈 Total Posts Analyzed: {result['total_posts']}")
            print(f"💡 Key Insight: {result['key_insight']}")
            
            if result['sentiment_summary']:
                print(f"📊 Sentiment Summary:")
                for sentiment, value in result['sentiment_summary'].items():
                    print(f"   {sentiment.capitalize()}: {value}%")
            
            if result['thematic_breakdown']:
                print(f"🎯 Thematic Breakdown:")
                for i, theme in enumerate(result['thematic_breakdown'][:5], 1):
                    print(f"   {i}. {theme}")
            
            if result['strategic_recommendations']:
                print(f"💼 Strategic Recommendations:")
                for i, rec in enumerate(result['strategic_recommendations'][:3], 1):
                    print(f"   {i}. {rec}")
            
            # Save HTML report
            if result['html_report']:
                report_file = f"report_{brand_data['name'].lower().replace(' ', '_')}.html"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(result['html_report'])
                print(f"\n📄 HTML report saved to: {report_file}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print("   Make sure you have APIFY_TOKEN and OPENAI_API_KEY in your .env file")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return False


async def multiple_brand_analysis():
    """Perform multiple brand analysis from Supabase."""
    print("\n📊 Multiple Brand Analysis")
    print("=" * 40)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Load brands from Supabase
        print("📖 Loading brands from Supabase...")
        result = supabase.table("prospects").select("*").execute()
        brands = result.data
        
        if not brands:
            print("❌ No brands found in Supabase database!")
            print("   Please add some brands to your 'prospects' table first.")
            return False
        
        print(f"📋 Found {len(brands)} brands to analyze:")
        for i, brand in enumerate(brands, 1):
            print(f"   {i}. {brand.get('brand_name', 'Unknown')} ({brand.get('industry_category', 'No category')})")
        
        # Confirm before proceeding
        print(f"\n⚠️  This will analyze {len(brands)} brands and may take a while.")
        confirm = input("🤔 Proceed with batch analysis? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Analysis cancelled.")
            return False
        
        # Perform real batch analysis
        print(f"\n🔍 Starting batch analysis of {len(brands)} brands...")
        print("   This will:")
        print("   1. Process each brand individually")
        print("   2. Search Reddit for each brand")
        print("   3. Analyze sentiment for each")
        print("   4. Generate insights and reports")
        print("   5. Save results to Supabase")
        
        try:
            # Initialize analyzer
            analyzer = RedditAnalyzer()
            
            # Process each brand
            results = []
            for i, brand in enumerate(brands, 1):
                brand_name = brand.get('brand_name', 'Unknown')
                print(f"\n📊 Processing brand {i}/{len(brands)}: {brand_name}")
                
                try:
                    result = await analyzer.analyze_brand(brand_name)
                    results.append(result)
                    print(f"   ✅ Completed: {result['total_posts']} posts analyzed")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    continue
            
            # Display results summary
            print(f"\n📊 Batch Analysis Results")
            print("=" * 50)
            print(f"✅ Successfully analyzed: {len(results)} brands")
            print(f"❌ Failed analyses: {len(brands) - len(results)} brands")
            
            if results:
                print(f"\n📋 Analysis Summary:")
                for result in results[:5]:  # Show first 5
                    print(f"   • {result['brand_name']}: {result['total_posts']} posts, Key insight: {result['key_insight'][:50]}...")
                
                if len(results) > 5:
                    print(f"   ... and {len(results) - 5} more brands")
                
                # Save results to Supabase (simplified for now)
                print(f"\n💾 Results would be saved to Supabase 'analysis_results' table")
                print("   (Supabase saving not implemented yet - results are in memory)")
            
        except Exception as e:
            print(f"❌ Batch analysis failed: {e}")
            print("   Make sure you have APIFY_TOKEN and OPENAI_API_KEY in your .env file")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Batch analysis failed: {e}")
        return False


async def view_prospects():
    """View prospects in the database."""
    print("\n🔍 Viewing Prospects in Database")
    print("=" * 40)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Load brands from Supabase
        print("📖 Loading prospects from Supabase...")
        result = supabase.table("prospects").select("*").execute()
        brands = result.data
        
        if not brands:
            print("❌ No prospects found in database!")
            print("   The 'prospects' table is empty.")
            print("   Add some prospects to your Supabase database first.")
        else:
            print(f"📊 Found {len(brands)} prospects in database:")
            print()
            for i, brand in enumerate(brands, 1):
                print(f"   {i}. {brand.get('brand_name', 'Unknown')}")
                if brand.get('industry_category'):
                    print(f"      Category: {brand['industry_category']}")
                if brand.get('website'):
                    print(f"      URL: {brand['website']}")
                if brand.get('hq_location'):
                    print(f"      Location: {brand['hq_location']}")
                print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to load prospects: {e}")
        return False


async def main():
    """Main menu loop."""
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
