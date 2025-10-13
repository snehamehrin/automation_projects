#!/usr/bin/env python3
"""
Brand Selection Workflow - Choose brand from prospects table
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brand_selection_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BrandSelectionWorkflow:
    """Handle brand selection from prospects table."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE credentials not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ BrandSelectionWorkflow initialized")
    
    def get_all_prospects(self) -> List[Dict[str, Any]]:
        """Get all prospects from the prospects table."""
        try:
            response = self.supabase.table('prospects').select('*').execute()
            
            if response.data:
                logger.info(f"📋 Found {len(response.data)} prospects")
                return response.data
            else:
                logger.info("📋 No prospects found")
                return []
                
        except Exception as e:
            logger.error(f"Error getting prospects: {e}")
            return []
    
    def search_prospects(self, search_term: str) -> List[Dict[str, Any]]:
        """Search prospects by name."""
        try:
            # Search in brand_name field (case insensitive)
            response = self.supabase.table('prospects').select('*').ilike('brand_name', f'%{search_term}%').execute()
            
            if response.data:
                logger.info(f"🔍 Found {len(response.data)} matching prospects for '{search_term}'")
                return response.data
            else:
                logger.info(f"🔍 No prospects found matching '{search_term}'")
                return []
                
        except Exception as e:
            logger.error(f"Error searching prospects: {e}")
            return []
    
    def display_prospect(self, prospect: Dict[str, Any]) -> None:
        """Display a prospect record in a nice format."""
        print(f"\n📊 Prospect Record:")
        print(f"=" * 50)
        print(f"ID: {prospect.get('id', 'N/A')}")
        print(f"Brand Name: {prospect.get('brand_name', 'N/A')}")
        print(f"Website: {prospect.get('website', 'N/A')}")
        print(f"Industry: {prospect.get('industry', 'N/A')}")
        print(f"Description: {prospect.get('description', 'N/A')}")
        print(f"Created: {prospect.get('created_at', 'N/A')}")
        print(f"=" * 50)
    
    def confirm_selection(self, prospect: Dict[str, Any]) -> bool:
        """Ask user to confirm the prospect selection."""
        print(f"\n❓ Do you want to proceed with this brand?")
        print(f"Brand: {prospect.get('brand_name', 'N/A')}")
        print(f"ID: {prospect.get('id', 'N/A')}")
        
        while True:
            choice = input("\nEnter 'y' to confirm, 'n' to cancel: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def update_google_results_with_prospect_id(self, prospect_id: str, brand_name: str) -> bool:
        """Update google_results table with prospect_id."""
        try:
            # Find records in google_results that match the brand name
            response = self.supabase.table('google_results').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                # Update each record with prospect_id
                for record in response.data:
                    update_response = self.supabase.table('google_results').update({
                        'prospect_id': prospect_id
                    }).eq('id', record['id']).execute()
                
                logger.info(f"✅ Updated {len(response.data)} records in google_results with prospect_id: {prospect_id}")
                return True
            else:
                logger.info(f"📋 No records found in google_results for brand: {brand_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating google_results: {e}")
            return False
    
    def update_brand_google_reddit_with_prospect_id(self, prospect_id: str, brand_name: str) -> bool:
        """Update brand_google_reddit table with prospect_id."""
        try:
            # Find records in brand_google_reddit that match the brand name
            response = self.supabase.table('brand_google_reddit').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                # Update each record with prospect_id
                for record in response.data:
                    update_response = self.supabase.table('brand_google_reddit').update({
                        'prospect_id': prospect_id
                    }).eq('id', record['id']).execute()
                
                logger.info(f"✅ Updated {len(response.data)} records in brand_google_reddit with prospect_id: {prospect_id}")
                return True
            else:
                logger.info(f"📋 No records found in brand_google_reddit for brand: {brand_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating brand_google_reddit: {e}")
            return False
    
    def update_brand_reddit_posts_comments_with_prospect_id(self, prospect_id: str, brand_name: str) -> bool:
        """Update brand_reddit_posts_comments table with prospect_id."""
        try:
            # Find records in brand_reddit_posts_comments that match the brand name
            response = self.supabase.table('brand_reddit_posts_comments').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                # Update each record with prospect_id
                for record in response.data:
                    update_response = self.supabase.table('brand_reddit_posts_comments').update({
                        'prospect_id': prospect_id
                    }).eq('id', record['id']).execute()
                
                logger.info(f"✅ Updated {len(response.data)} records in brand_reddit_posts_comments with prospect_id: {prospect_id}")
                return True
            else:
                logger.info(f"📋 No records found in brand_reddit_posts_comments for brand: {brand_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating brand_reddit_posts_comments: {e}")
            return False
    
    def run_brand_selection_workflow(self):
        """Run the complete brand selection workflow."""
        print("🚀 Brand Selection Workflow")
        print("=" * 40)
        
        while True:
            print("\nOptions:")
            print("1. Search for a brand")
            print("2. List all prospects")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                self._handle_search_workflow()
            elif choice == "2":
                self._handle_list_workflow()
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def _handle_search_workflow(self):
        """Handle the search workflow."""
        search_term = input("\nEnter brand name to search: ").strip()
        
        if not search_term:
            print("❌ Please enter a search term")
            return
        
        prospects = self.search_prospects(search_term)
        
        if not prospects:
            print(f"❌ No prospects found matching '{search_term}'")
            return
        
        if len(prospects) == 1:
            # Single match - show and confirm
            prospect = prospects[0]
            self.display_prospect(prospect)
            
            if self.confirm_selection(prospect):
                self._update_all_tables(prospect)
            else:
                print("❌ Selection cancelled")
        else:
            # Multiple matches - let user choose
            print(f"\n📋 Found {len(prospects)} matching prospects:")
            for i, prospect in enumerate(prospects, 1):
                print(f"{i}. {prospect.get('brand_name', 'N/A')} (ID: {prospect.get('id', 'N/A')})")
            
            try:
                choice = int(input(f"\nEnter choice (1-{len(prospects)}): ").strip())
                if 1 <= choice <= len(prospects):
                    prospect = prospects[choice - 1]
                    self.display_prospect(prospect)
                    
                    if self.confirm_selection(prospect):
                        self._update_all_tables(prospect)
                    else:
                        print("❌ Selection cancelled")
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def _handle_list_workflow(self):
        """Handle the list all prospects workflow."""
        prospects = self.get_all_prospects()
        
        if not prospects:
            print("❌ No prospects found")
            return
        
        print(f"\n📋 All Prospects ({len(prospects)} total):")
        for i, prospect in enumerate(prospects, 1):
            print(f"{i}. {prospect.get('brand_name', 'N/A')} (ID: {prospect.get('id', 'N/A')})")
        
        try:
            choice = int(input(f"\nEnter choice (1-{len(prospects)}): ").strip())
            if 1 <= choice <= len(prospects):
                prospect = prospects[choice - 1]
                self.display_prospect(prospect)
                
                if self.confirm_selection(prospect):
                    self._update_all_tables(prospect)
                else:
                    print("❌ Selection cancelled")
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def _update_all_tables(self, prospect: Dict[str, Any]):
        """Update all tables with the prospect_id."""
        prospect_id = prospect.get('id')
        brand_name = prospect.get('brand_name')
        
        if not prospect_id or not brand_name:
            print("❌ Invalid prospect data")
            return
        
        print(f"\n🔄 Updating tables with prospect_id: {prospect_id}")
        print(f"Brand: {brand_name}")
        
        # Update all tables
        google_results_updated = self.update_google_results_with_prospect_id(prospect_id, brand_name)
        brand_google_reddit_updated = self.update_brand_google_reddit_with_prospect_id(prospect_id, brand_name)
        reddit_posts_updated = self.update_brand_reddit_posts_comments_with_prospect_id(prospect_id, brand_name)
        
        # Summary
        print(f"\n📊 Update Summary:")
        print(f"✅ google_results: {'Updated' if google_results_updated else 'No records found'}")
        print(f"✅ brand_google_reddit: {'Updated' if brand_google_reddit_updated else 'No records found'}")
        print(f"✅ brand_reddit_posts_comments: {'Updated' if reddit_posts_updated else 'No records found'}")
        
        print(f"\n🎉 Brand selection workflow completed!")
        print(f"Prospect ID: {prospect_id}")
        print(f"Brand: {brand_name}")


if __name__ == "__main__":
    try:
        workflow = BrandSelectionWorkflow()
        workflow.run_brand_selection_workflow()
    except Exception as e:
        logger.error(f"Error: {e}")
