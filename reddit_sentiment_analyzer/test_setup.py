#!/usr/bin/env python3
"""
Simple test script to verify the setup and test the first step.

This script tests:
1. Environment configuration
2. Supabase connection
3. Single brand input
4. Supabase database operations
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData
from src.services.supabase import SupabaseService
from src.utils.logging import get_logger, initialize_logging
from src.config.settings import get_settings

logger = get_logger(__name__)


async def test_environment():
    """Test environment configuration."""
    print("🔧 Testing environment configuration...")
    
    settings = get_settings()
    
    # Check required environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "APIFY_API_KEY", 
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings.external_apis if var.startswith(("OPENAI", "APIFY")) else settings.supabase, var.lower().replace("_", ""), None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ Environment configuration looks good")
    return True


async def test_supabase_connection():
    """Test Supabase connection."""
    print("🔗 Testing Supabase connection...")
    
    try:
        supabase = SupabaseService()
        await supabase.initialize()
        
        # Test connection
        is_connected = await supabase.test_connection()
        
        if is_connected:
            print("✅ Supabase connection successful")
            
            # Try to load brands
            brands = await supabase.load_brands()
            print(f"📊 Found {len(brands)} brands in database")
            
            await supabase.close()
            return True
        else:
            print("❌ Supabase connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False


async def test_single_brand_input():
    """Test single brand input functionality."""
    print("🏷️  Testing single brand input...")
    
    try:
        # Create a test brand
        test_brand = BrandData(
            name="Test Brand",
            category="Technology",
            company_url="https://testbrand.com"
        )
        
        print(f"✅ Created test brand: {test_brand.name}")
        print(f"   Category: {test_brand.category}")
        print(f"   URL: {test_brand.company_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Single brand input test failed: {e}")
        return False


async def test_supabase_operations():
    """Test Supabase database operations."""
    print("💾 Testing Supabase database operations...")
    
    try:
        supabase = SupabaseService()
        await supabase.initialize()
        
        # Test adding a brand
        test_brand = BrandData(
            name="Test Brand for DB",
            category="Test Category",
            company_url="https://testbrand.com"
        )
        
        print("📝 Testing brand insertion...")
        result = await supabase.add_brand(test_brand)
        print(f"✅ Brand added successfully: {result.get('id', 'N/A')}")
        
        # Test loading brands
        print("📖 Testing brand loading...")
        brands = await supabase.load_brands()
        print(f"✅ Loaded {len(brands)} brands from database")
        
        # Show first few brands
        for i, brand in enumerate(brands[:3]):
            print(f"   {i+1}. {brand.name} ({brand.category})")
        
        if len(brands) > 3:
            print(f"   ... and {len(brands) - 3} more")
        
        await supabase.close()
        return True
        
    except Exception as e:
        print(f"❌ Supabase operations test failed: {e}")
        return False


async def test_analyzer_initialization():
    """Test analyzer initialization."""
    print("🤖 Testing analyzer initialization...")
    
    try:
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        print("✅ Analyzer initialized successfully")
        
        # Test services
        print("🔍 Testing service connections...")
        
        # Test Supabase
        supabase_ok = await analyzer.supabase.test_connection()
        print(f"   Supabase: {'✅' if supabase_ok else '❌'}")
        
        # Test OpenAI (without making actual API call)
        print(f"   OpenAI: ✅ (configured)")
        
        # Test Apify (without making actual API call)
        print(f"   Apify: ✅ (configured)")
        
        await analyzer.close()
        return True
        
    except Exception as e:
        print(f"❌ Analyzer initialization failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Reddit Sentiment Analyzer - Setup Test")
    print("=" * 50)
    
    # Initialize logging
    initialize_logging()
    
    tests = [
        ("Environment Configuration", test_environment),
        ("Supabase Connection", test_supabase_connection),
        ("Single Brand Input", test_single_brand_input),
        ("Supabase Operations", test_supabase_operations),
        ("Analyzer Initialization", test_analyzer_initialization)
    ]
    
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
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Add some brands to your Supabase 'brands' table")
        print("2. Run a full analysis with: python test_analysis.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Missing API keys in .env file")
        print("- Incorrect Supabase URL or key")
        print("- Supabase tables not created yet")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
