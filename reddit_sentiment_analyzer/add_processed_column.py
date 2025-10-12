#!/usr/bin/env python3
"""
Add processed column to brand_google_reddit table
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


def add_processed_column():
    """Add processed column to brand_google_reddit table."""
    print("🔧 Adding processed column to brand_google_reddit table")
    print("=" * 60)
    
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_KEY not found")
        return
    
    # Initialize Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    print("📋 SQL to add processed column:")
    print("""
    ALTER TABLE brand_google_reddit 
    ADD COLUMN processed BOOLEAN DEFAULT FALSE;
    
    -- Create index for faster queries
    CREATE INDEX idx_brand_google_reddit_processed ON brand_google_reddit(processed);
    """)
    
    print("\n🔧 Please run this SQL in your Supabase SQL Editor to add the processed column.")
    print("   This will track which URLs have been scraped for Reddit data.")


if __name__ == "__main__":
    add_processed_column()
