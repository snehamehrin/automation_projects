#!/usr/bin/env python3
"""
Check processing status of URLs in brand_google_reddit table
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client


async def check_processing_status():
    """Check how many URLs are processed vs unprocessed."""
    print("📊 Checking Processing Status")
    print("=" * 50)
    
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found")
        return
    
    # Initialize Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Get total count
        total_response = supabase.table('brand_google_reddit').select('id', count='exact').execute()
        total_count = total_response.count
        
        # Get processed count
        processed_response = supabase.table('brand_google_reddit').select('id', count='exact').eq('processed', True).execute()
        processed_count = processed_response.count
        
        # Get unprocessed count
        unprocessed_response = supabase.table('brand_google_reddit').select('id', count='exact').eq('processed', False).execute()
        unprocessed_count = unprocessed_response.count
        
        print(f"📈 Total URLs: {total_count}")
        print(f"✅ Processed: {processed_count}")
        print(f"⏳ Unprocessed: {unprocessed_count}")
        
        if total_count > 0:
            processed_percentage = (processed_count / total_count) * 100
            print(f"📊 Progress: {processed_percentage:.1f}% complete")
        
        # Show breakdown by brand
        print(f"\n📋 Breakdown by Brand:")
        brand_response = supabase.table('brand_google_reddit').select('brand_name, processed').execute()
        
        brand_stats = {}
        for item in brand_response.data:
            brand = item['brand_name']
            if brand not in brand_stats:
                brand_stats[brand] = {'total': 0, 'processed': 0}
            brand_stats[brand]['total'] += 1
            if item['processed']:
                brand_stats[brand]['processed'] += 1
        
        for brand, stats in brand_stats.items():
            percentage = (stats['processed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   {brand}: {stats['processed']}/{stats['total']} ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(check_processing_status())
