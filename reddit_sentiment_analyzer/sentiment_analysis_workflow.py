#!/usr/bin/env python3
"""
Sentiment Analysis Workflow - Main entry point
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
        logging.FileHandler('sentiment_analysis_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SentimentAnalysisWorkflow:
    """Main sentiment analysis workflow."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE credentials not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ SentimentAnalysisWorkflow initialized")
    
    def search_prospects(self, brand_name: str) -> List[Dict[str, Any]]:
        """Search prospects by brand name."""
        try:
            # Search in brand_name field (case insensitive)
            response = self.supabase.table('prospects').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                logger.info(f"🔍 Found {len(response.data)} matching prospects for '{brand_name}'")
                return response.data
            else:
                logger.info(f"🔍 No prospects found matching '{brand_name}'")
                return []
                
        except Exception as e:
            logger.error(f"Error searching prospects: {e}")
            return []
    
    def display_prospects(self, prospects: List[Dict[str, Any]]) -> None:
        """Display prospects in a nice format."""
        print(f"\n📊 Found {len(prospects)} matching prospects:")
        print("=" * 60)
        
        for i, prospect in enumerate(prospects, 1):
            print(f"{i}. Brand: {prospect.get('brand_name', 'N/A')}")
            print(f"   ID: {prospect.get('id', 'N/A')}")
            print(f"   Website: {prospect.get('website', 'N/A')}")
            print(f"   Industry: {prospect.get('industry', 'N/A')}")
            print()
    
    def create_prospect(self, brand_name: str) -> Dict[str, Any]:
        """Create a new prospect entry."""
        try:
            prospect_data = {
                'brand_name': brand_name,
                'website': '',  # Will be filled later if available
                'industry': '',
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('prospects').insert(prospect_data).execute()
            
            if response.data:
                prospect = response.data[0]
                logger.info(f"✅ Created new prospect: {brand_name} (ID: {prospect['id']})")
                return prospect
            else:
                logger.error("❌ Failed to create prospect")
                return None
                
        except Exception as e:
            logger.error(f"Error creating prospect: {e}")
            return None
    
    def select_prospect(self, prospects: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Let user select a prospect."""
        if len(prospects) == 1:
            # Single match - auto-select
            prospect = prospects[0]
            print(f"✅ Auto-selected: {prospect.get('brand_name', 'N/A')} (ID: {prospect.get('id', 'N/A')})")
            return prospect
        
        # Multiple matches - let user choose
        self.display_prospects(prospects)
        
        while True:
            try:
                choice = int(input(f"\nEnter choice (1-{len(prospects)}): ").strip())
                if 1 <= choice <= len(prospects):
                    return prospects[choice - 1]
                else:
                    print(f"❌ Please enter a number between 1 and {len(prospects)}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def get_prospect_for_brand(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Get or create prospect for a brand."""
        # Search for existing prospects
        prospects = self.search_prospects(brand_name)
        
        if prospects:
            # Found matches - let user select
            return self.select_prospect(prospects)
        else:
            # No matches - create new prospect
            print(f"❌ No prospects found for '{brand_name}'")
            create_new = input("Create new prospect? (y/n): ").strip().lower()
            
            if create_new in ['y', 'yes']:
                return self.create_prospect(brand_name)
            else:
                print("❌ Cancelled")
                return None
    
    def update_tables_with_prospect_id(self, prospect_id: str, brand_name: str) -> bool:
        """Update all tables with prospect_id during scraping."""
        try:
            # This will be called during the scraping process
            # For now, just log that we'll use this prospect_id
            logger.info(f"🔄 Will use prospect_id: {prospect_id} for brand: {brand_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tables: {e}")
            return False
    
    def run_sentiment_analysis_for_brand(self, brand_name: str):
        """Run sentiment analysis for a specific brand."""
        print(f"\n🚀 Starting Sentiment Analysis for: {brand_name}")
        print("=" * 50)
        
        # Get or create prospect
        prospect = self.get_prospect_for_brand(brand_name)
        
        if not prospect:
            print("❌ No prospect selected. Exiting.")
            return
        
        prospect_id = prospect.get('id')
        prospect_brand_name = prospect.get('brand_name')
        
        print(f"\n✅ Selected Prospect:")
        print(f"   Brand: {prospect_brand_name}")
        print(f"   ID: {prospect_id}")
        
        # Now run the complete analysis with this prospect_id
        self._run_complete_analysis_with_prospect(prospect_id, prospect_brand_name)
    
    def run_sentiment_analysis_for_all_prospects(self):
        """Run sentiment analysis for all prospects."""
        print(f"\n🚀 Starting Sentiment Analysis for ALL Prospects")
        print("=" * 50)
        
        try:
            # Get all prospects
            response = self.supabase.table('prospects').select('*').execute()
            
            if not response.data:
                print("❌ No prospects found")
                return
            
            prospects = response.data
            print(f"📊 Found {len(prospects)} prospects to analyze")
            
            for i, prospect in enumerate(prospects, 1):
                prospect_id = prospect.get('id')
                brand_name = prospect.get('brand_name')
                
                print(f"\n🔄 Processing {i}/{len(prospects)}: {brand_name}")
                print("-" * 40)
                
                # Run analysis for this prospect
                self._run_complete_analysis_with_prospect(prospect_id, brand_name)
                
                # Ask if user wants to continue
                if i < len(prospects):
                    continue_choice = input(f"\nContinue to next prospect? (y/n): ").strip().lower()
                    if continue_choice not in ['y', 'yes']:
                        print("⏹️ Stopping analysis")
                        break
            
            print(f"\n🎉 Completed analysis for all prospects!")
            
        except Exception as e:
            logger.error(f"Error in all prospects analysis: {e}")
    
    def _run_complete_analysis_with_prospect(self, prospect_id: str, brand_name: str):
        """Run the complete analysis pipeline with prospect_id."""
        try:
            # Import and run the complete analysis
            from complete_reddit_analysis import CompleteRedditAnalyzer
            
            analyzer = CompleteRedditAnalyzer()
            
            # Run analysis with prospect_id
            import asyncio
            asyncio.run(analyzer.run_complete_analysis(prospect_id=prospect_id, limit=10))
            
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
    
    def run_main_workflow(self):
        """Run the main workflow."""
        print("🚀 Sentiment Analysis Workflow")
        print("=" * 40)
        
        # Use default choice for testing
        choice = "1"  # Enter a brand name
        brand_name = "Knix"  # We know this exists
        
        print(f"\nOptions:")
        print("1. Enter a brand name")
        print("2. Run sentiment analysis for entire prospects")
        print("3. Exit")
        print(f"\nUsing choice: {choice} with brand: {brand_name}")
        
        if choice == "1":
            self.run_sentiment_analysis_for_brand(brand_name)
        elif choice == "2":
            self.run_sentiment_analysis_for_all_prospects()
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice.")


if __name__ == "__main__":
    try:
        workflow = SentimentAnalysisWorkflow()
        workflow.run_main_workflow()
    except Exception as e:
        logger.error(f"Error: {e}")
