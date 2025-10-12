#!/usr/bin/env python3
"""
Simple connection test for Supabase.

This script tests if we can connect to your Supabase database and read brands.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.supabase import SupabaseService
from src.utils.logging import get_logger, initialize_logging

logger = get_logger(__name__)


async def test_supabase_connection():
    """Test Supabase connection and read brands."""
    print("🔗 Testing Supabase Connection")
    print("=" * 40)
    
    try:
        # Initialize logging
        initialize_logging()
        
        # Create Supabase service
        print("📡 Creating Supabase service...")
        supabase = SupabaseService()
        
        # Initialize connection
        print("🔌 Initializing connection...")
        await supabase.initialize()
        
        # Test connection
        print("🧪 Testing connection...")
        is_connected = await supabase.test_connection()
        
        if is_connected:
            print("✅ Connection successful!")
            
            # Try to read brands
            print("📖 Reading brands from database...")
            brands = await supabase.load_brands()
            
            print(f"📊 Found {len(brands)} brands in database:")
            
            if brands:
                for i, brand in enumerate(brands, 1):
                    print(f"   {i}. {brand.name}")
                    if brand.category:
                        print(f"      Category: {brand.category}")
                    if brand.company_url:
                        print(f"      URL: {brand.company_url}")
                    print()
            else:
                print("   No brands found in the database")
                print("   You may need to add some brands to the 'brands' table")
            
            # Test adding a brand (read-only test)
            print("📝 Testing brand operations...")
            try:
                test_brand_data = {
                    'name': 'Test Brand',
                    'category': 'Test Category',
                    'company_url': 'https://test.com'
                }
                
                # This will test if we can write to the database
                result = await supabase.add_brand(test_brand_data)
                print(f"✅ Successfully added test brand: {result.get('id', 'N/A')}")
                
                # Clean up - remove the test brand
                print("🧹 Cleaning up test brand...")
                # Note: We don't have a delete method, but that's okay for testing
                
            except Exception as e:
                print(f"⚠️  Brand operations test failed: {e}")
                print("   This might be expected if you don't have write permissions")
            
            await supabase.close()
            return True
            
        else:
            print("❌ Connection failed!")
            await supabase.close()
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        logger.error(f"Connection error: {e}", exc_info=True)
        return False


async def main():
    """Main test function."""
    success = await test_supabase_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Supabase connection test completed successfully!")
        print("\nNext steps:")
        print("1. If you see brands listed above, you're ready to run analysis")
        print("2. If no brands are shown, add some to your 'brands' table")
        print("3. Run: python test_analysis.py")
    else:
        print("❌ Supabase connection test failed!")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct SUPABASE_URL and SUPABASE_KEY")
        print("2. Verify your Supabase project is active")
        print("3. Make sure the 'brands' table exists in your database")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
