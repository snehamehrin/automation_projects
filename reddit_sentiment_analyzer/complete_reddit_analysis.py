#!/usr/bin/env python3
"""
Complete Reddit Analysis Pipeline - Replicating n8n workflow
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

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
        logging.FileHandler('complete_reddit_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompleteRedditAnalyzer:
    """Complete Reddit analysis pipeline replicating n8n workflow."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY not found")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE credentials not found")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.apify_base_url = "https://api.apify.com/v2"
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.openai_key)
        
        logger.info("✅ CompleteRedditAnalyzer initialized")
    
    async def run_complete_analysis(self, brand_name: str = None, prospect_id: str = None, limit: int = 5):
        """Run the complete analysis pipeline."""
        logger.info("🚀 Starting Complete Reddit Analysis Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Get Reddit data from database (already scraped)
        reddit_data = await self.get_reddit_data_from_db(brand_name, prospect_id, limit)
        if not reddit_data:
            logger.warning("No Reddit data found in database")
            return
        
        logger.info(f"📊 Found {len(reddit_data)} Reddit items in database")
        
        # Step 2: Filter and clean data (from n8n Code2)
        filtered_data = self.filter_reddit_data(reddit_data)
        logger.info(f"📊 After filtering: {len(filtered_data)} items")
        
        # Step 4: Normalize data (from n8n Normalize Code)
        normalized_data = self.normalize_data(filtered_data)
        logger.info(f"📊 After normalization: {len(normalized_data)} items")
        
        # Step 5: Remove duplicates (from n8n De-Dupe Posts)
        deduplicated_data = self.remove_duplicates(normalized_data)
        logger.info(f"📊 After deduplication: {len(deduplicated_data)} items")
        
        # Step 6: Trim and prepare for AI analysis (from n8n Trim Posts)
        trimmed_data = self.trim_posts(deduplicated_data)
        logger.info(f"📊 After trimming: {len(trimmed_data)} items")
        
        # Step 3: Generate AI analysis (from n8n Generate Prompt + Message a model)
        if trimmed_data:
            # Get brand name from the data
            actual_brand_name = trimmed_data[0].get('brand_name', brand_name or "Brand")
            analysis_result = await self.generate_ai_analysis(trimmed_data, actual_brand_name)
            
            # Step 4: Save results
            await self.save_analysis_results(analysis_result, reddit_data)
        
        logger.info("🎉 Complete analysis pipeline finished!")
    
    async def get_reddit_data_from_db(self, brand_name: str = None, prospect_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get Reddit posts and comments from database."""
        try:
            query = self.supabase.table('brand_reddit_posts_comments').select('*')
            
            if prospect_id:
                query = query.eq('prospect_id', prospect_id)
            elif brand_name:
                query = query.eq('brand_name', brand_name)
            
            query = query.limit(limit)
            
            response = query.execute()
            if response.data:
                logger.info(f"📋 Found {len(response.data)} Reddit posts/comments from database")
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting Reddit data: {e}")
            return []
    
    async def scrape_reddit_url(self, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        """Scrape Reddit URL using Apify."""
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
                return response.json()
            else:
                logger.error(f"Apify error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []
    
    def filter_reddit_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter Reddit data (from n8n Code2)."""
        filter_patterns = {
            'bot': [
                "i am a bot", "action was performed automatically", "contact the moderators",
                "automoderator", "bot, and this action", "performed automatically",
                "/message/compose/?to=", "if you have any questions or concerns"
            ],
            'deleted': ["[deleted]", "[removed]", "deleted by user", "removed by moderator"],
            'moderator': [
                "#### about participation", "discussion in this subreddit", "please vote accordingly",
                "removal or ban territory", "good - it is grounded in science", "bad - it utilizes generalizations"
            ],
            'welcome': ["welcome to", "thanks for joining", "new to the sub", "first time posting"],
            'spam': ["check out my", "follow me on", "link in bio", "dm me for", "click here"]
        }
        
        filtered = []
        for item in data:
            text = (item.get('body', '') + ' ' + item.get('title', '')).lower()
            
            # Skip empty or very short text
            if not text or len(text.strip()) < 3:
                continue
            
            # Check for filter patterns
            should_skip = False
            for category, patterns in filter_patterns.items():
                if any(pattern in text for pattern in patterns):
                    should_skip = True
                    break
            
            if not should_skip:
                filtered.append(item)
        
        return filtered
    
    def normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize data (from n8n Normalize Code)."""
        normalized = []
        for item in data:
            text = (item.get('body', '') or '').strip()
            if len(text) < 20:  # Skip very short text
                continue
            
            normalized_item = {
                'id': item.get('id', ''),
                'text': text,
                'subreddit': item.get('communityName', ''),
                'createdAt': item.get('createdAt', ''),
                'upVotes': item.get('upVotes', 0),
                'url': item.get('url', ''),
                'brandName': item.get('brandName', ''),
                'dataType': item.get('dataType', '')
            }
            normalized.append(normalized_item)
        
        return normalized
    
    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates (from n8n De-Dupe Posts)."""
        seen = set()
        unique = []
        
        for item in data:
            key = (item.get('url', '') + '|' + item.get('text', '')[:160])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique
    
    def trim_posts(self, data: List[Dict[str, Any]], max_text: int = 1200, max_posts: int = 120) -> List[Dict[str, Any]]:
        """Trim posts (from n8n Trim Posts)."""
        # Limit text length
        trimmed = []
        for item in data:
            item['text'] = item.get('text', '')[:max_text]
            trimmed.append(item)
        
        # Limit number of posts
        return trimmed[:max_posts]
    
    async def generate_ai_analysis(self, data: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """Generate AI analysis (from n8n Generate Prompt + Message a model)."""
        logger.info("🤖 Generating AI analysis...")
        
        # Prepare data for analysis
        posts_string = json.dumps(data)[:180000]  # Limit size
        
        prompt = f"""Analyze the Reddit posts/comments about {brand_name} and create a comprehensive Brand Intelligence Report as a visual HTML artifact using CROSS-DOMAIN PATTERN RECOGNITION.

You are an expert in behavioral science, cultural anthropology, and AI-powered consumer psychology. Apply these lenses to find hidden patterns others miss.

DATA (array of posts):
{posts_string}

KEY INSIGHT GENERATION RULES:
Your KEY_INSIGHT must follow this formula: [Brand] faces a "[specific behavioral/psychological phenomenon]" - [specific percentage] of [specific behavior], [cross-domain framework explains why], particularly [specific audience segment].

HTML STRUCTURE REQUIREMENTS - Follow this EXACT format:

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brand Intelligence Report - {brand_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .header {{ background: #FFD700; color: #000; padding: 40px; text-align: center; margin-bottom: 20px; }}
        .header h1 {{ font-size: 2.5em; margin: 0; }}
        .header h2 {{ font-size: 1.2em; margin: 10px 0 0 0; }}
        .stats-container {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #FFD700; color: #000; padding: 20px; text-align: center; flex: 1; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; }}
        .stat-label {{ font-size: 1em; }}
        .section {{ background: #fff; margin: 20px 0; padding: 20px; border-left: 5px solid #FFD700; }}
        .section-title {{ background: #FFD700; color: #000; padding: 15px; margin: -20px -20px 20px -20px; font-size: 1.5em; font-weight: bold; }}
        .key-insight {{ background: #000; color: #FFD700; padding: 20px; margin: 20px 0; font-size: 1.2em; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #FFD700; color: #000; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BRAND INTELLIGENCE REPORT</h1>
        <h2>{brand_name.upper()} - Reddit Consumer Intelligence Analysis</h2>
        <p>Total Analyzed: {len(data)} Posts & Comments | Analysis Period: Recent Reddit Activity</p>
    </div>

    <div class="section">
        <div class="section-title">EXECUTIVE SUMMARY</div>
        <div class="key-insight">
            KEY INSIGHT: [Your cross-domain behavioral insight here following the formula]
        </div>
    </div>

    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">{len(data)}</div>
            <div class="stat-label">TOTAL POSTS</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">[X]%</div>
            <div class="stat-label">POSITIVE</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">[X]%</div>
            <div class="stat-label">NEGATIVE</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">[X]%</div>
            <div class="stat-label">NEUTRAL</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Thematic Breakdown</div>
        <table>
            <tr><th>Theme</th><th>Mentions</th><th>Sentiment</th><th>Strategic Insight</th></tr>
            [Table rows with thematic analysis]
        </table>
    </div>

    <div class="section">
        <div class="section-title">Customer Segment Clues</div>
        [Customer segment analysis]
    </div>

    <div class="section">
        <div class="section-title">Strategic Recommendations</div>
        [Strategic recommendations based on insights]
    </div>

    <div class="section">
        <div class="section-title">Bottom Line Intelligence</div>
        <h4>Executive Summary</h4>
        <p><strong>The Challenge:</strong> [Core behavioral/psychological challenge]</p>
        <p><strong>The Opportunity:</strong> [Strategic opportunity based on cross-domain insights]</p>
        <p><strong>Priority Actions:</strong> [3 specific actionable recommendations]</p>
    </div>
</body>
</html>

ANALYSIS REQUIREMENTS:
1. Apply behavioral science frameworks (loss aversion, social proof, cognitive biases)
2. Identify cultural/anthropological patterns (tribal behavior, status signaling, identity formation)
3. Use AI language analysis for subconscious motivation detection
4. Connect to economic behavior principles (Veblen goods, network effects, switching costs)
5. Focus on cross-domain insights that reveal hidden patterns

CRITICAL OUTPUT FORMAT:
<BRAND_NAME>
{brand_name}
</BRAND_NAME>
<KEY_INSIGHT>
[Brand] faces a "[behavioral phenomenon]" - [percentage] of [specific behavior], [cross-domain explanation], particularly [audience segment]
</KEY_INSIGHT>
<HTML_REPORT>
[Complete HTML following the exact structure above]
</HTML_REPORT>"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a consumer insight strategist. Your job is to analyze Reddit posts about a specific brand and extract strategic intelligence. Your goal is not just to summarize sentiment, but to uncover themes, identify growth opportunities, detect customer confusion, map customer journeys, and suggest actionable tests. Be strategic and structured. You are writing a report for the brand's CMO and Head of Product."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Extract structured data
            brand_match = content.split('<BRAND_NAME>')[1].split('</BRAND_NAME>')[0].strip() if '<BRAND_NAME>' in content else brand_name
            insight_match = content.split('<KEY_INSIGHT>')[1].split('</KEY_INSIGHT>')[0].strip() if '<KEY_INSIGHT>' in content else "No key insight found"
            html_match = content.split('<HTML_REPORT>')[1].split('</HTML_REPORT>')[0].strip() if '<HTML_REPORT>' in content else content
            
            return {
                'brandName': brand_match,
                'keyInsight': insight_match,
                'htmlContent': html_match,
                'rawContent': content,
                'analysisDate': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                'brandName': brand_name,
                'keyInsight': "Analysis failed",
                'htmlContent': f"<p>Analysis failed: {str(e)}</p>",
                'rawContent': "",
                'analysisDate': datetime.now().isoformat()
            }
    
    async def save_analysis_results(self, analysis_result: Dict[str, Any], reddit_data: List[Dict[str, Any]]):
        """Save analysis results to database."""
        logger.info("💾 Saving analysis results to database...")
        
        try:
            # Prepare data for database - only the 4 required fields
            result_data = {
                'brand_name': analysis_result['brandName'],
                'key_insight': analysis_result['keyInsight'],
                'html_content': analysis_result['htmlContent'],
                'analysis_date': analysis_result['analysisDate']
            }
            
            # Save to database
            response = self.supabase.table('reddit_brand_analysis_results').insert(result_data).execute()
            
            if response.data:
                analysis_id = response.data[0]['id']
                logger.info(f"✅ Analysis results saved to database with ID: {analysis_id}")
                
                # Print summary for easy access
                print(f"\n🎉 Analysis Complete!")
                print(f"=" * 50)
                print(f"Brand: {analysis_result['brandName']}")
                print(f"Key Insight: {analysis_result['keyInsight']}")
                print(f"Database ID: {analysis_id}")
                print(f"\n📊 Database Storage:")
                print(f"   Table: brand_analysis_results")
                print(f"   ID: {analysis_id}")
                print(f"   Fields: brand_name, key_insight, html_content, analysis_date")
                print(f"\n🌐 For Replit: Query the database for ID {analysis_id}")
                
                return analysis_id
            else:
                logger.error("❌ Failed to save analysis results to database")
                return None
                
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            return None
    
async def main():
    """Main function."""
    try:
        analyzer = CompleteRedditAnalyzer()
        
        print("🚀 Reddit Analysis Pipeline")
        print("=" * 40)
        print("1. Analyze by brand name")
        print("2. Analyze by prospect ID")
        print("3. Analyze all data")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            brand_name = input("Enter brand name: ").strip()
            if not brand_name:
                print("❌ Brand name is required")
                return
            limit = input("Enter limit (default 10): ").strip()
            limit = int(limit) if limit else 10
            
            logger.info(f"🚀 Starting analysis with brand_name={brand_name}, limit={limit}")
            await analyzer.run_complete_analysis(brand_name=brand_name, limit=limit)
            
        elif choice == "2":
            prospect_id = input("Enter prospect ID: ").strip()
            if not prospect_id:
                print("❌ Prospect ID is required")
                return
            limit = input("Enter limit (default 10): ").strip()
            limit = int(limit) if limit else 10
            
            logger.info(f"🚀 Starting analysis with prospect_id={prospect_id}, limit={limit}")
            await analyzer.run_complete_analysis(prospect_id=prospect_id, limit=limit)
            
        elif choice == "3":
            limit = input("Enter limit (default 10): ").strip()
            limit = int(limit) if limit else 10
            
            logger.info(f"🚀 Starting analysis with all data, limit={limit}")
            await analyzer.run_complete_analysis(limit=limit)
            
        else:
            print("❌ Invalid choice")
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
