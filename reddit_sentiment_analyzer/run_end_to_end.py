#!/usr/bin/env python3
"""
End-to-End Sentiment Analysis Workflow
1. Search for brand in prospects
2. Update all tables with prospect_id
3. Scrape Reddit data
4. Run AI analysis
5. Save results
"""

import asyncio
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
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('end_to_end_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EndToEndWorkflow:
    """Complete end-to-end sentiment analysis workflow."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.apify_base_url = "https://api.apify.com/v2"
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY not found")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE credentials not found")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ EndToEndWorkflow initialized")
    
    def search_and_select_prospect(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Search for a brand and return the prospect."""
        logger.info(f"🔍 Searching for brand: {brand_name}")
        
        try:
            response = self.supabase.table('prospects').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                prospects = response.data
                logger.info(f"✅ Found {len(prospects)} matching prospects")
                
                for prospect in prospects:
                    logger.info(f"   - {prospect.get('brand_name')} (ID: {prospect.get('id')})")
                
                # Auto-select first match
                selected = prospects[0]
                logger.info(f"✅ Auto-selected: {selected.get('brand_name')}")
                return selected
            else:
                logger.warning(f"❌ No prospects found for '{brand_name}'")
                return None
                
        except Exception as e:
            logger.error(f"Error searching prospects: {e}")
            return None
    
    def update_tables_with_prospect_id(self, prospect_id: str, brand_name: str) -> bool:
        """Update all tables with prospect_id."""
        logger.info(f"🔄 Updating tables with prospect_id: {prospect_id}")
        
        tables_updated = 0
        
        # Update brand_google_reddit
        try:
            response = self.supabase.table('brand_google_reddit').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            if response.data:
                for record in response.data:
                    self.supabase.table('brand_google_reddit').update({
                        'prospect_id': prospect_id
                    }).eq('id', record['id']).execute()
                logger.info(f"✅ Updated {len(response.data)} records in brand_google_reddit")
                tables_updated += 1
        except Exception as e:
            logger.error(f"Error updating brand_google_reddit: {e}")
        
        # Update brand_reddit_posts_comments
        try:
            response = self.supabase.table('brand_reddit_posts_comments').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            if response.data:
                for record in response.data:
                    self.supabase.table('brand_reddit_posts_comments').update({
                        'prospect_id': prospect_id
                    }).eq('id', record['id']).execute()
                logger.info(f"✅ Updated {len(response.data)} records in brand_reddit_posts_comments")
                tables_updated += 1
        except Exception as e:
            logger.error(f"Error updating brand_reddit_posts_comments: {e}")
        
        return tables_updated > 0
    
    async def get_reddit_urls_to_scrape(self, prospect_id: str, brand_name: str) -> List[Dict[str, Any]]:
        """Get Reddit URLs that need to be scraped."""
        logger.info(f"🔍 Getting Reddit URLs for {brand_name}")
        
        try:
            # Get URLs from brand_google_reddit that haven't been processed
            response = self.supabase.table('brand_google_reddit').select('*').eq('prospect_id', prospect_id).eq('processed', False).limit(5).execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} URLs to scrape")
                return response.data
            else:
                logger.info("📋 No unprocessed URLs found")
                return []
                
        except Exception as e:
            logger.error(f"Error getting URLs: {e}")
            return []
    
    async def scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL using Apify."""
        logger.info(f"🔍 Scraping Reddit URL: {url}")
        
        try:
            payload = {
                "startUrls": [{"url": url}],
                "maxPosts": 1,
                "maxComments": 1000,
                "maxCommunitiesCount": 1,
                "scrollTimeout": 60,
                "proxy": {"useApifyProxy": True}
            }
            
            response = await client.post(
                f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                headers={"Authorization": f"Bearer {self.apify_token}"},
                json=payload,
                timeout=120.0
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ Successfully scraped {len(data)} items from {url}")
                return data
            else:
                logger.error(f"❌ Error scraping Reddit: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Exception during scraping: {e}")
            return []
    
    def process_reddit_data(self, reddit_data: list, brand_name: str, prospect_id: str) -> list:
        """Process Reddit data into the correct format for database."""
        logger.info(f"🔄 Processing {len(reddit_data)} Reddit items for brand: {brand_name}")
        processed_data = []
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
                title = item.get('title', '')
                body = item.get('body', '')
                full_text = f"{title}. {body}".strip()
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('id', ''),
                    'parent_id': None,
                    'category': 'post',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('commentsCount', 0),
                    'data_type': 'post',
                    'brand_name': brand_name,
                    'body': full_text,
                    'prospect_id': prospect_id
                }
                processed_data.append(processed_item)
                
            elif item.get('dataType') == 'comment':
                comment_body = item.get('body', '')
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),
                    'parent_id': item.get('parentId', ''),
                    'category': 'comment',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfreplies', 0),
                    'data_type': 'comment',
                    'brand_name': brand_name,
                    'body': comment_body,
                    'prospect_id': prospect_id
                }
                processed_data.append(processed_item)
        
        logger.info(f"✅ Processed {len(processed_data)} items")
        return processed_data
    
    async def save_reddit_data(self, reddit_data: list) -> bool:
        """Save Reddit data to brand_reddit_posts_comments table."""
        if not reddit_data:
            logger.warning("No data to save")
            return False
            
        logger.info(f"💾 Saving {len(reddit_data)} items to database...")
        try:
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                logger.info(f"✅ Successfully saved {len(response.data)} items to database")
                return True
            else:
                logger.error("❌ No data returned from database insert")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            return False
    
    async def mark_urls_as_processed(self, url_ids: list) -> bool:
        """Mark URLs as processed in the brand_google_reddit table."""
        if not url_ids:
            return True
            
        logger.info(f"🏷️ Marking {len(url_ids)} URLs as processed...")
        try:
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            
            if response.data:
                logger.info(f"✅ Marked {len(response.data)} URLs as processed")
                return True
            else:
                logger.error("❌ Failed to mark URLs as processed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error marking URLs as processed: {e}")
            return False
    
    async def get_reddit_data_for_analysis(self, prospect_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Reddit data for analysis."""
        try:
            response = self.supabase.table('brand_reddit_posts_comments').select('*').eq('prospect_id', prospect_id).limit(limit).execute()
            
            if response.data:
                logger.info(f"📋 Found {len(response.data)} Reddit posts/comments for analysis")
                return response.data
            else:
                logger.info("📋 No Reddit data found for analysis")
                return []
                
        except Exception as e:
            logger.error(f"Error getting Reddit data: {e}")
            return []
    
    async def generate_ai_analysis(self, data: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """Generate AI analysis using OpenAI."""
        logger.info("🤖 Generating AI analysis...")
        
        try:
            import openai
            openai_client = openai.OpenAI(api_key=self.openai_key)
            
            # Prepare data for analysis
            posts_string = ""
            for i, post in enumerate(data, 1):
                posts_string += f"POST {i}:\n"
                posts_string += f"Type: {post.get('data_type', 'unknown')}\n"
                posts_string += f"Community: {post.get('community_name', 'unknown')}\n"
                posts_string += f"Upvotes: {post.get('up_votes', 0)}\n"
                posts_string += f"Content: {post.get('body', '')}\n\n"
            
            prompt = f"""
Analyze the following Reddit data for {brand_name} and provide insights.

DATA:
{posts_string}

Provide a key insight and HTML report. Return as JSON with keys: keyInsight, htmlContent
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a brand intelligence analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            logger.info(f"✅ AI analysis generated successfully")
            
            try:
                result = json.loads(content)
                return {
                    'brandName': brand_name,
                    'keyInsight': result.get('keyInsight', 'Analysis completed'),
                    'htmlContent': result.get('htmlContent', '<p>Analysis completed</p>'),
                    'analysisDate': datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                return {
                    'brandName': brand_name,
                    'keyInsight': f"{brand_name} shows mixed sentiment in Reddit discussions",
                    'htmlContent': f'<html><body><h1>{brand_name} Analysis</h1><p>{content}</p></body></html>',
                    'analysisDate': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                'brandName': brand_name,
                'keyInsight': f"Analysis failed for {brand_name}",
                'htmlContent': f"<p>Analysis failed: {str(e)}</p>",
                'analysisDate': datetime.now().isoformat()
            }
    
    async def save_analysis_results(self, analysis_result: Dict[str, Any], prospect_id: str) -> bool:
        """Save analysis results to database."""
        logger.info("💾 Saving analysis results to database...")
        
        try:
            result_data = {
                'brand_name': analysis_result['brandName'],
                'key_insight': analysis_result['keyInsight'],
                'html_content': analysis_result['htmlContent'],
                'analysis_date': analysis_result['analysisDate'],
                'prospect_id': prospect_id
            }
            
            response = self.supabase.table('reddit_brand_analysis_results').insert(result_data).execute()
            
            if response.data:
                analysis_id = response.data[0]['id']
                logger.info(f"✅ Analysis results saved to database with ID: {analysis_id}")
                
                print(f"\n🎉 Analysis Complete!")
                print(f"=" * 50)
                print(f"Brand: {analysis_result['brandName']}")
                print(f"Key Insight: {analysis_result['keyInsight']}")
                print(f"Database ID: {analysis_id}")
                print(f"Prospect ID: {prospect_id}")
                
                return True
            else:
                logger.error("❌ Failed to save analysis results to database")
                return False
                
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            return False
    
    def show_menu(self):
        """Show the main menu options."""
        print("🚀 End-to-End Sentiment Analysis Workflow")
        print("=" * 50)
        print("Options:")
        print("1. Enter a brand name")
        print("2. Run analysis for all prospects")
        print("3. Exit")
        
        # Use default choice for testing
        choice = "1"  # Enter a brand name
        print(f"\nUsing choice: {choice} (Enter a brand name)")
        return choice
    
    async def run_complete_workflow(self):
        """Run the complete end-to-end workflow."""
        logger.info("🚀 Starting Complete End-to-End Workflow")
        logger.info("=" * 60)
        
        # Show menu and get user choice
        choice = self.show_menu()
        
        if choice == "3":
            print("👋 Goodbye!")
            return
        
        if choice == "1":
            # Use default brand name for testing
            brand_name = "Knix"  # We know this exists
            print(f"Using brand name: {brand_name}")
            
            # Run workflow for single brand
            await self.run_workflow_for_brand(brand_name)
            
        elif choice == "2":
            # Run workflow for all prospects
            await self.run_workflow_for_all_prospects()
    
    async def run_workflow_for_brand(self, brand_name: str):
        """Run workflow for a single brand."""
        # Step 1: Search and select prospect
        prospect = self.search_and_select_prospect(brand_name)
        if not prospect:
            logger.error("❌ No prospect found. Exiting.")
            return
        
        prospect_id = prospect.get('id')
        prospect_brand_name = prospect.get('brand_name')
        
        logger.info(f"✅ Selected Prospect: {prospect_brand_name} (ID: {prospect_id})")
        
        # Step 2: Update tables with prospect_id
        self.update_tables_with_prospect_id(prospect_id, prospect_brand_name)
        
        # Step 3: Get URLs to scrape
        urls_to_scrape = await self.get_reddit_urls_to_scrape(prospect_id, prospect_brand_name)
        
        if urls_to_scrape:
            # Step 4: Scrape Reddit data
            logger.info(f"🔍 Scraping {len(urls_to_scrape)} Reddit URLs...")
            
            all_reddit_data = []
            processed_url_ids = []
            
            async with httpx.AsyncClient() as client:
                for url_data in urls_to_scrape:
                    url = url_data['url']
                    url_id = url_data['id']
                    
                    reddit_data = await self.scrape_reddit_url(client, url)
                    if reddit_data:
                        processed_data = self.process_reddit_data(reddit_data, prospect_brand_name, prospect_id)
                        all_reddit_data.extend(processed_data)
                        processed_url_ids.append(url_id)
            
            # Step 5: Save Reddit data
            if all_reddit_data:
                await self.save_reddit_data(all_reddit_data)
                await self.mark_urls_as_processed(processed_url_ids)
        
        # Step 6: Get Reddit data for analysis
        reddit_data_for_analysis = await self.get_reddit_data_for_analysis(prospect_id, limit=10)
        
        if reddit_data_for_analysis:
            # Step 7: Generate AI analysis
            analysis_result = await self.generate_ai_analysis(reddit_data_for_analysis, prospect_brand_name)
            
            # Step 8: Save analysis results
            await self.save_analysis_results(analysis_result, prospect_id)
        else:
            logger.warning("❌ No Reddit data available for analysis")
        
        logger.info("🎉 End-to-end workflow completed!")
    
    async def run_workflow_for_all_prospects(self):
        """Run workflow for all prospects."""
        logger.info("🚀 Running workflow for all prospects")
        
        try:
            # Get all prospects
            response = self.supabase.table('prospects').select('*').execute()
            
            if not response.data:
                logger.error("❌ No prospects found")
                return
            
            prospects = response.data
            logger.info(f"📊 Found {len(prospects)} prospects to process")
            
            for i, prospect in enumerate(prospects, 1):
                prospect_id = prospect.get('id')
                brand_name = prospect.get('brand_name')
                
                print(f"\n🔄 Processing {i}/{len(prospects)}: {brand_name}")
                print("-" * 40)
                
                # Run workflow for this prospect
                await self.run_workflow_for_prospect(prospect)
                
                # Ask if user wants to continue
                if i < len(prospects):
                    continue_choice = input(f"\nContinue to next prospect? (y/n): ").strip().lower()
                    if continue_choice not in ['y', 'yes']:
                        print("⏹️ Stopping workflow")
                        break
            
            print(f"\n🎉 Completed workflow for all prospects!")
            
        except Exception as e:
            logger.error(f"Error in all prospects workflow: {e}")
    
    async def run_workflow_for_prospect(self, prospect: Dict[str, Any]):
        """Run workflow for a specific prospect."""
        prospect_id = prospect.get('id')
        prospect_brand_name = prospect.get('brand_name')
        
        logger.info(f"✅ Processing Prospect: {prospect_brand_name} (ID: {prospect_id})")
        
        # Update tables with prospect_id
        self.update_tables_with_prospect_id(prospect_id, prospect_brand_name)
        
        # Get URLs to scrape
        urls_to_scrape = await self.get_reddit_urls_to_scrape(prospect_id, prospect_brand_name)
        
        if urls_to_scrape:
            # Scrape Reddit data
            logger.info(f"🔍 Scraping {len(urls_to_scrape)} Reddit URLs...")
            
            all_reddit_data = []
            processed_url_ids = []
            
            async with httpx.AsyncClient() as client:
                for url_data in urls_to_scrape:
                    url = url_data['url']
                    url_id = url_data['id']
                    
                    reddit_data = await self.scrape_reddit_url(client, url)
                    if reddit_data:
                        processed_data = self.process_reddit_data(reddit_data, prospect_brand_name, prospect_id)
                        all_reddit_data.extend(processed_data)
                        processed_url_ids.append(url_id)
            
            # Save Reddit data
            if all_reddit_data:
                await self.save_reddit_data(all_reddit_data)
                await self.mark_urls_as_processed(processed_url_ids)
        
        # Get Reddit data for analysis
        reddit_data_for_analysis = await self.get_reddit_data_for_analysis(prospect_id, limit=10)
        
        if reddit_data_for_analysis:
            # Generate AI analysis
            analysis_result = await self.generate_ai_analysis(reddit_data_for_analysis, prospect_brand_name)
            
            # Save analysis results
            await self.save_analysis_results(analysis_result, prospect_id)
        else:
            logger.warning(f"❌ No Reddit data available for analysis for {prospect_brand_name}")


async def main():
    """Main function."""
    try:
        workflow = EndToEndWorkflow()
        await workflow.run_complete_workflow()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
