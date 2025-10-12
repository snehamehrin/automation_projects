#!/usr/bin/env python3
"""
Test script for running actual sentiment analysis.

This script tests the complete analysis pipeline:
1. Single brand analysis
2. Supabase database analysis
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData
from src.utils.logging import get_logger, initialize_logging

logger = get_logger(__name__)


async def test_single_brand_analysis():
    """Test single brand analysis."""
    print("🏷️  Testing single brand analysis...")
    
    try:
        # Create analyzer
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Create test brand
        test_brand = BrandData(
            name="Nike",
            category="Sportswear",
            company_url="https://www.nike.com"
        )
        
        print(f"🎯 Analyzing brand: {test_brand.name}")
        print(f"📂 Category: {test_brand.category}")
        print(f"🌐 URL: {test_brand.company_url}")
        
        # Perform analysis
        print("🔄 Starting analysis... (this may take a few minutes)")
        result = await analyzer.analyze_brand(test_brand)
        
        # Display results
        print("\n📊 Analysis Results:")
        print(f"   Brand: {result.brand_name}")
        print(f"   Total Posts: {result.total_posts}")
        print(f"   Key Insight: {result.key_insight}")
        
        if result.sentiment_summary:
            print("   Sentiment Summary:")
            for sentiment, value in result.sentiment_summary.items():
                print(f"     {sentiment.capitalize()}: {value}")
        
        if result.thematic_breakdown:
            print("   Thematic Breakdown:")
            for i, theme in enumerate(result.thematic_breakdown[:3], 1):
                print(f"     {i}. {theme}")
        
        if result.strategic_recommendations:
            print("   Strategic Recommendations:")
            for i, rec in enumerate(result.strategic_recommendations[:3], 1):
                print(f"     {i}. {rec}")
        
        # Save HTML report
        if result.html_report:
            report_file = f"report_{test_brand.name.lower().replace(' ', '_')}.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(result.html_report)
            print(f"\n📄 HTML report saved to: {report_file}")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"❌ Single brand analysis failed: {e}")
        logger.error(f"Analysis error: {e}", exc_info=True)
        return False


async def test_supabase_analysis():
    """Test analysis from Supabase database."""
    print("💾 Testing Supabase database analysis...")
    
    try:
        # Create analyzer
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        # Load brands from Supabase
        print("📖 Loading brands from Supabase...")
        brands = await analyzer.supabase.load_brands()
        
        if not brands:
            print("⚠️  No brands found in Supabase database")
            print("   Please add some brands to the 'brands' table first")
            return False
        
        print(f"📊 Found {len(brands)} brands to analyze")
        
        # Analyze first brand only (to save time and API costs)
        if len(brands) > 1:
            print(f"🎯 Analyzing first brand only: {brands[0].name}")
            brands_to_analyze = [brands[0]]
        else:
            brands_to_analyze = brands
        
        # Perform analysis
        print("🔄 Starting analysis... (this may take a few minutes)")
        results = await analyzer.analyze_brands_batch(brands_to_analyze)
        
        # Display results
        print(f"\n📊 Analysis Results ({len(results)} brands):")
        for result in results:
            print(f"\n   Brand: {result.brand_name}")
            print(f"   Total Posts: {result.total_posts}")
            print(f"   Key Insight: {result.key_insight[:100]}...")
        
        # Results should be automatically saved to Supabase
        print("\n💾 Results have been saved to Supabase 'analysis_results' table")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"❌ Supabase analysis failed: {e}")
        logger.error(f"Analysis error: {e}", exc_info=True)
        return False


async def main():
    """Main test function."""
    print("🚀 Reddit Sentiment Analyzer - Analysis Test")
    print("=" * 50)
    
    # Initialize logging
    initialize_logging()
    
    print("Choose test to run:")
    print("1. Single brand analysis (Nike)")
    print("2. Supabase database analysis")
    print("3. Both tests")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        tests = [("Single Brand Analysis", test_single_brand_analysis)]
    elif choice == "2":
        tests = [("Supabase Analysis", test_supabase_analysis)]
    elif choice == "3":
        tests = [
            ("Single Brand Analysis", test_single_brand_analysis),
            ("Supabase Analysis", test_supabase_analysis)
        ]
    else:
        print("❌ Invalid choice")
        return False
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All analysis tests passed!")
        print("\nYour Reddit Sentiment Analyzer is working correctly!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)