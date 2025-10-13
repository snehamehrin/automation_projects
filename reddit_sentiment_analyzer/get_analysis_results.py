#!/usr/bin/env python3
"""
Get analysis results from database
"""

import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Get credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

def get_latest_analysis(brand_name: str = None):
    """Get the latest analysis results."""
    try:
        query = supabase.table('brand_analysis_results').select('*')
        
        if brand_name:
            query = query.eq('brand_name', brand_name)
        
        query = query.order('analysis_date', desc=True).limit(1)
        response = query.execute()
        
        if response.data:
            result = response.data[0]
            print(f"📊 Latest Analysis Results")
            print(f"=" * 50)
            print(f"Brand: {result['brand_name']}")
            print(f"Analysis Date: {result['analysis_date']}")
            print(f"Database ID: {result['id']}")
            print(f"\n🔑 Key Insight:")
            print(f"{result['key_insight']}")
            print(f"\n📄 HTML Content Length: {len(result['html_content'])} characters")
            
            return result
        else:
            print("❌ No analysis results found")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_all_analyses():
    """Get all analysis results."""
    try:
        response = supabase.table('brand_analysis_results').select('*').order('analysis_date', desc=True).execute()
        
        if response.data:
            print(f"📊 All Analysis Results ({len(response.data)} total)")
            print(f"=" * 50)
            
            for i, result in enumerate(response.data, 1):
                print(f"{i}. Brand: {result['brand_name']}")
                print(f"   ID: {result['id']}")
                print(f"   Date: {result['analysis_date']}")
                print(f"   Key Insight: {result['key_insight'][:100]}...")
                print()
            
            return response.data
        else:
            print("❌ No analysis results found")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def get_analysis_by_id(analysis_id: str):
    """Get specific analysis by ID."""
    try:
        response = supabase.table('brand_analysis_results').select('*').eq('id', analysis_id).execute()
        
        if response.data:
            result = response.data[0]
            print(f"📊 Analysis Results for ID: {analysis_id}")
            print(f"=" * 50)
            print(f"Brand: {result['brand_name']}")
            print(f"Analysis Date: {result['analysis_date']}")
            print(f"\n🔑 Key Insight:")
            print(f"{result['key_insight']}")
            print(f"\n📄 HTML Content:")
            print(f"{result['html_content']}")
            
            return result
        else:
            print(f"❌ No analysis found with ID: {analysis_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def save_html_to_file(analysis_id: str, filename: str = None):
    """Save HTML content to file."""
    try:
        response = supabase.table('brand_analysis_results').select('html_content, brand_name').eq('id', analysis_id).execute()
        
        if response.data:
            result = response.data[0]
            html_content = result['html_content']
            brand_name = result['brand_name']
            
            if not filename:
                filename = f"{brand_name.lower().replace(' ', '_')}_report.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML report saved to: {filename}")
            return filename
        else:
            print(f"❌ No analysis found with ID: {analysis_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Analysis Results Viewer")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Get latest analysis")
        print("2. Get all analyses")
        print("3. Get analysis by ID")
        print("4. Save HTML to file")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            brand = input("Enter brand name (or press Enter for any): ").strip()
            if not brand:
                brand = None
            get_latest_analysis(brand)
            
        elif choice == "2":
            get_all_analyses()
            
        elif choice == "3":
            analysis_id = input("Enter analysis ID: ").strip()
            get_analysis_by_id(analysis_id)
            
        elif choice == "4":
            analysis_id = input("Enter analysis ID: ").strip()
            filename = input("Enter filename (or press Enter for default): ").strip()
            if not filename:
                filename = None
            save_html_to_file(analysis_id, filename)
            
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")
