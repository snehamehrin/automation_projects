#!/usr/bin/env python3
"""
Correct End-to-End Workflow:
1. Ask for brand input
2. Check prospects table and ask for confirmation
3. Run Google search to get Reddit URLs and update with prospect_id
4. Scrape Reddit data from URLs and save with prospect_id
5. Run AI analysis on the data
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
import openai

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('correct_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CorrectWorkflow:
    """Correct end-to-end workflow."""
    
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
        self.openai_client = openai.OpenAI(api_key=self.openai_key)
        logger.info("✅ CorrectWorkflow initialized")
    
    def show_menu(self):
        """Show the main menu options."""
        print("🚀 Sentiment Analysis Workflow")
        print("=" * 40)
        print("Options:")
        print("1. Enter a brand name")
        print("2. Run analysis for all prospects")
        print("3. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                return choice
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def search_and_confirm_prospect(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Search for brand in prospects table and ask for confirmation."""
        print(f"\n🔍 Searching for brand: {brand_name}")
        
        try:
            response = self.supabase.table('prospects').select('*').ilike('brand_name', f'%{brand_name}%').execute()
            
            if response.data:
                prospects = response.data
                print(f"\n📊 Found {len(prospects)} matching prospects:")
                print("=" * 50)
                
                for i, prospect in enumerate(prospects, 1):
                    print(f"{i}. Brand: {prospect.get('brand_name', 'N/A')}")
                    print(f"   ID: {prospect.get('id', 'N/A')}")
                    print(f"   Website: {prospect.get('website', 'N/A')}")
                    print()
                
                if len(prospects) == 1:
                    # Single match - ask for confirmation
                    prospect = prospects[0]
                    print(f"✅ Found exact match: {prospect.get('brand_name')}")
                    confirm = input(f"Proceed with this brand? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return prospect
                    else:
                        print("❌ Cancelled")
                        return None
                else:
                    # Multiple matches - let user choose
                    try:
                        choice = int(input(f"Enter choice (1-{len(prospects)}): ").strip())
                        if 1 <= choice <= len(prospects):
                            return prospects[choice - 1]
                        else:
                            print("❌ Invalid choice")
                            return None
                    except ValueError:
                        print("❌ Please enter a valid number")
                        return None
            else:
                print(f"❌ No prospects found for '{brand_name}'")
                create_new = input("Create new prospect? (y/n): ").strip().lower()
                if create_new in ['y', 'yes']:
                    return self.create_prospect(brand_name)
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching prospects: {e}")
            return None
    
    def create_prospect(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Create a new prospect."""
        try:
            prospect_data = {
                'brand_name': brand_name,
                'website': '',
                'industry': '',
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('prospects').insert(prospect_data).execute()
            
            if response.data:
                prospect = response.data[0]
                print(f"✅ Created new prospect: {brand_name} (ID: {prospect['id']})")
                return prospect
            else:
                print("❌ Failed to create prospect")
                return None
                
        except Exception as e:
            logger.error(f"Error creating prospect: {e}")
            return None
    
    async def run_google_search(self, brand_name: str, prospect_id: str) -> bool:
        """Run Google search to get Reddit URLs and save with prospect_id."""
        print(f"\n🔍 Running Google search for: {brand_name}")
        
        try:
            # Use Apify Google Search Scraper
            payload = {
                "queries": [f"{brand_name} reddit"],
                "maxResultsPerQuery": 10,
                "resultsType": "urls",
                "countryCode": "us",
                "languageCode": "en"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.apify_base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    json=payload,
                    timeout=120.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    print(f"✅ Found {len(data)} search results")
                    
                    # Filter for Reddit URLs and save to brand_google_reddit table
                    reddit_urls = []
                    for item in data:
                        url = item.get('url', '')
                        if 'reddit.com' in url:
                            reddit_urls.append({
                                'url': url,
                                'title': item.get('title', ''),
                                'description': item.get('description', ''),
                                'brand_name': brand_name,
                                'prospect_id': prospect_id,
                                'processed': False,
                                'created_at': datetime.now().isoformat()
                            })
                    
                    if reddit_urls:
                        # Save to database
                        db_response = self.supabase.table('brand_google_reddit').insert(reddit_urls).execute()
                        if db_response.data:
                            print(f"✅ Saved {len(db_response.data)} Reddit URLs to database")
                            return True
                        else:
                            print("❌ Failed to save URLs to database")
                            return False
                    else:
                        print("❌ No Reddit URLs found in search results")
                        return False
                else:
                    print(f"❌ Google search failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error in Google search: {e}")
            return False
    
    async def scrape_reddit_urls(self, prospect_id: str, brand_name: str) -> bool:
        """Scrape Reddit URLs and save data with prospect_id."""
        print(f"\n🔍 Scraping Reddit URLs for: {brand_name}")
        
        try:
            # Get unprocessed URLs
            response = self.supabase.table('brand_google_reddit').select('*').eq('prospect_id', prospect_id).eq('processed', False).limit(5).execute()
            
            if not response.data:
                print("❌ No unprocessed URLs found")
                return False
            
            urls = response.data
            print(f"📋 Found {len(urls)} URLs to scrape")
            
            all_reddit_data = []
            processed_url_ids = []
            
            async with httpx.AsyncClient() as client:
                for url_data in urls:
                    url = url_data['url']
                    url_id = url_data['id']
                    
                    print(f"🔍 Scraping: {url}")
                    
                    # Scrape Reddit data
                    reddit_data = await self.scrape_reddit_url(client, url)
                    if reddit_data:
                        processed_data = self.process_reddit_data(reddit_data, brand_name, prospect_id)
                        all_reddit_data.extend(processed_data)
                        processed_url_ids.append(url_id)
                        print(f"✅ Scraped {len(processed_data)} items")
                    else:
                        print(f"❌ No data scraped from {url}")
            
            # Save Reddit data
            if all_reddit_data:
                await self.save_reddit_data(all_reddit_data)
                await self.mark_urls_as_processed(processed_url_ids)
                print(f"✅ Saved {len(all_reddit_data)} Reddit items to database")
                return True
            else:
                print("❌ No Reddit data to save")
                return False
                
        except Exception as e:
            logger.error(f"Error scraping Reddit URLs: {e}")
            return False
    
    async def scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape a single Reddit URL using Apify."""
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
                return data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error scraping Reddit URL: {e}")
            return []
    
    def process_reddit_data(self, reddit_data: list, brand_name: str, prospect_id: str) -> list:
        """Process Reddit data into the correct format for database."""
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
        
        return processed_data
    
    async def save_reddit_data(self, reddit_data: list) -> bool:
        """Save Reddit data to brand_reddit_posts_comments table."""
        try:
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error saving Reddit data: {e}")
            return False
    
    async def mark_urls_as_processed(self, url_ids: list) -> bool:
        """Mark URLs as processed in the brand_google_reddit table."""
        try:
            response = self.supabase.table('brand_google_reddit').update({
                'processed': True
            }).in_('id', url_ids).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error marking URLs as processed: {e}")
            return False
    
    async def run_ai_analysis(self, prospect_id: str, brand_name: str) -> bool:
        """Run AI analysis on Reddit data."""
        print(f"\n🤖 Running AI analysis for: {brand_name}")
        
        try:
            # Get Reddit data for analysis
            response = self.supabase.table('brand_reddit_posts_comments').select('*').eq('prospect_id', prospect_id).limit(10).execute()
            
            if not response.data:
                print("❌ No Reddit data found for analysis")
                return False
            
            data = response.data
            print(f"📊 Analyzing {len(data)} Reddit items")
            
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
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a brand intelligence analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                key_insight = result.get('keyInsight', 'Analysis completed')
                html_content = result.get('htmlContent', '<p>Analysis completed</p>')
            except json.JSONDecodeError:
                key_insight = f"{brand_name} shows mixed sentiment in Reddit discussions"
                html_content = f'<html><body><h1>{brand_name} Analysis</h1><p>{content}</p></body></html>'
            
            # Save analysis results
            result_data = {
                'brand_name': brand_name,
                'key_insight': key_insight,
                'html_content': html_content,
                'analysis_date': datetime.now().isoformat(),
                'prospect_id': prospect_id
            }
            
            db_response = self.supabase.table('reddit_brand_analysis_results').insert(result_data).execute()
            
            if db_response.data:
                analysis_id = db_response.data[0]['id']
                print(f"✅ Analysis saved with ID: {analysis_id}")
                print(f"\n🎉 Analysis Complete!")
                print(f"=" * 50)
                print(f"Brand: {brand_name}")
                print(f"Key Insight: {key_insight}")
                print(f"Database ID: {analysis_id}")
                return True
            else:
                print("❌ Failed to save analysis results")
                return False
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return False
    
    async def run_workflow_for_brand(self, brand_name: str):
        """Run complete workflow for a single brand."""
        print(f"\n🚀 Starting workflow for: {brand_name}")
        print("=" * 50)
        
        # Step 1: Search and confirm prospect
        prospect = self.search_and_confirm_prospect(brand_name)
        if not prospect:
            print("❌ No prospect selected. Exiting.")
            return
        
        prospect_id = prospect.get('id')
        prospect_brand_name = prospect.get('brand_name')
        
        print(f"✅ Selected Prospect: {prospect_brand_name} (ID: {prospect_id})")
        
        # Step 2: Run Google search
        if not await self.run_google_search(prospect_brand_name, prospect_id):
            print("❌ Google search failed. Exiting.")
            return
        
        # Step 3: Scrape Reddit URLs
        if not await self.scrape_reddit_urls(prospect_id, prospect_brand_name):
            print("❌ Reddit scraping failed. Exiting.")
            return
        
        # Step 4: Run AI analysis
        if not await self.run_ai_analysis(prospect_id, prospect_brand_name):
            print("❌ AI analysis failed.")
            return
        
        print(f"\n🎉 Complete workflow finished for {prospect_brand_name}!")
    
    async def run_workflow_for_all_prospects(self):
        """Run workflow for all prospects."""
        print(f"\n🚀 Running workflow for all prospects")
        
        try:
            response = self.supabase.table('prospects').select('*').execute()
            
            if not response.data:
                print("❌ No prospects found")
                return
            
            prospects = response.data
            print(f"📊 Found {len(prospects)} prospects to process")
            
            for i, prospect in enumerate(prospects, 1):
                brand_name = prospect.get('brand_name')
                print(f"\n🔄 Processing {i}/{len(prospects)}: {brand_name}")
                print("-" * 40)
                
                await self.run_workflow_for_brand(brand_name)
                
                if i < len(prospects):
                    continue_choice = input(f"\nContinue to next prospect? (y/n): ").strip().lower()
                    if continue_choice not in ['y', 'yes']:
                        print("⏹️ Stopping workflow")
                        break
            
            print(f"\n🎉 Completed workflow for all prospects!")
            
        except Exception as e:
            logger.error(f"Error in all prospects workflow: {e}")
    
    async def run_main_workflow(self):
        """Run the main workflow."""
        choice = self.show_menu()
        
        if choice == "1":
            brand_name = input("\nEnter brand name: ").strip()
            if not brand_name:
                print("❌ Brand name is required")
                return
            await self.run_workflow_for_brand(brand_name)
            
        elif choice == "2":
            await self.run_workflow_for_all_prospects()
            
        elif choice == "3":
            print("👋 Goodbye!")


async def main():
    """Main function."""
    try:
        workflow = CorrectWorkflow()
        await workflow.run_main_workflow()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
