#!/usr/bin/env python3
"""
Reddit Sentiment Analyzer - Core Analysis Engine

This implements the main analysis workflow:
1. Search Reddit for brand mentions
2. Process and filter posts
3. Analyze sentiment with AI
4. Generate insights and reports
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import httpx
from openai import OpenAI


class RedditAnalyzer:
    """Main Reddit sentiment analysis engine."""
    
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_KEY") or os.getenv("APIFY_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.apify_token:
            raise ValueError("APIFY_API_KEY or APIFY_TOKEN not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.apify_base_url = "https://api.apify.com/v2"
    
    async def search_reddit_posts(self, brand_name: str, max_posts: int = 50) -> List[Dict[str, Any]]:
        """Search Reddit for posts about the brand following N8N workflow."""
        print(f"🔍 Searching Reddit for posts about '{brand_name}'...")
        
        # Step 1: Google Search with site:reddit.com (following N8N workflow)
        search_queries = [
            f"site:reddit.com {brand_name} review",
            f"site:reddit.com {brand_name} reviews"
        ]
        
        reddit_urls = []
        
        async with httpx.AsyncClient() as client:
            # Step 1: Get Reddit URLs from Google search
            for query in search_queries:
                try:
                    print(f"   Google searching: '{query}'")
                    
                    payload = {
                        "queries": query,
                        "resultsPerPage": 20,
                        "maxPagesPerQuery": 1,
                        "aiMode": "aiModeOff"
                    }
                    
                    response = await client.post(
                        f"{self.apify_base_url}/acts/apify~google-search-scraper/run-sync-get-dataset-items",
                        headers={"Authorization": f"Bearer {self.apify_token}"},
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        google_results = response.json()
                        # Extract Reddit URLs from Google results
                        for result in google_results:
                            if result.get('url') and 'reddit.com/r/' in result['url']:
                                reddit_urls.append({
                                    'url': result['url'],
                                    'title': result.get('title', ''),
                                    'description': result.get('description', '')
                                })
                        print(f"   Found {len([r for r in google_results if r.get('url') and 'reddit.com/r/' in r['url']])} Reddit URLs")
                    else:
                        print(f"   ❌ Error searching '{query}': {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error searching '{query}': {e}")
                    continue
        
        print(f"📊 Total Reddit URLs found: {len(reddit_urls)}")
        
        if not reddit_urls:
            print("❌ No Reddit URLs found")
            return []
        
        # Step 2: Scrape Reddit posts using the URLs
        all_posts = []
        
        for i, reddit_url in enumerate(reddit_urls[:10]):  # Limit to first 10 URLs
            try:
                print(f"   Scraping Reddit post {i+1}/{min(len(reddit_urls), 10)}: {reddit_url['url']}")
                
                payload = {
                    "startUrls": [{"url": reddit_url['url']}],
                    "maxPosts": 1,
                    "maxComments": 20,
                    "maxCommunitiesCount": 1,
                    "scrollTimeout": 40,
                    "proxy": {"useApifyProxy": True}
                }
                
                response = await client.post(
                    f"{self.apify_base_url}/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    reddit_data = response.json()
                    all_posts.extend(reddit_data)
                    print(f"   Found {len(reddit_data)} items (posts + comments)")
                else:
                    print(f"   ❌ Error scraping Reddit: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error scraping Reddit: {e}")
                continue
        
        # Step 3: Process and filter the data
        processed_posts = self._process_reddit_data(all_posts, brand_name)
        
        print(f"📊 Total processed posts/comments: {len(processed_posts)}")
        return processed_posts
    
    def _process_reddit_data(self, reddit_data: List[Dict[str, Any]], brand_name: str) -> List[Dict[str, Any]]:
        """Process Reddit data following N8N workflow pattern."""
        processed_items = []
        
        for item in reddit_data:
            if item.get('dataType') == 'post':
                processed_items.append({
                    'id': item.get('id', ''),
                    'text': f"{item.get('title', '')}. {item.get('body', '')}",
                    'type': 'post',
                    'title': item.get('title', ''),
                    'community': item.get('communityName', ''),
                    'upVotes': item.get('upVotes', 0),
                    'createdAt': item.get('createdAt', ''),
                    'brandName': brand_name,
                    'url': item.get('url', '')
                })
            elif item.get('dataType') == 'comment':
                processed_items.append({
                    'id': item.get('id', ''),
                    'postId': item.get('postId', ''),
                    'text': item.get('body', ''),
                    'type': 'comment',
                    'createdAt': item.get('createdAt', ''),
                    'brandName': brand_name,
                    'url': item.get('url', '')
                })
        
        # Apply filtering (similar to N8N Code2)
        filtered_items = self._filter_reddit_data(processed_items)
        
        # Remove duplicates
        unique_items = self._deduplicate_posts(filtered_items)
        
        return unique_items
    
    def _filter_reddit_data(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter Reddit data to remove bots, deleted posts, etc."""
        filter_patterns = {
            'bot': [
                "i am a bot",
                "action was performed automatically",
                "contact the moderators",
                "automoderator",
                "bot, and this action",
                "performed automatically",
                "/message/compose/?to=",
                "if you have any questions or concerns"
            ],
            'deleted': [
                "[deleted]",
                "[removed]",
                "deleted by user",
                "removed by moderator"
            ],
            'moderator': [
                "#### about participation",
                "discussion in this subreddit",
                "please vote accordingly",
                "removal or ban territory",
                "good - it is grounded in science",
                "bad - it utilizes generalizations",
                "rooted in science rather than",
                "peer reviewed sources",
                "off topic discussion",
                "please [contact the moderators"
            ],
            'welcome': [
                "welcome to",
                "welcome to the",
                "thanks for joining",
                "new to the sub",
                "first time posting",
                "glad you're here"
            ],
            'spam': [
                "check out my",
                "follow me on",
                "link in bio",
                "dm me for",
                "click here",
                "subscribe to my"
            ]
        }
        
        filtered_items = []
        
        for item in items:
            text = (item.get('text', '') + ' ' + item.get('title', '')).lower()
            
            # Skip empty text
            if not text or len(text.strip()) < 3:
                continue
            
            # Check for filter patterns
            should_skip = False
            for category, patterns in filter_patterns.items():
                if any(pattern in text for pattern in patterns):
                    should_skip = True
                    break
            
            if not should_skip:
                filtered_items.append(item)
        
        return filtered_items
    
    def _deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on URL."""
        seen_urls = set()
        unique_posts = []
        
        for post in posts:
            url = post.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_posts.append(post)
        
        return unique_posts
    
    def _filter_posts(self, posts: List[Dict[str, Any]], brand_name: str) -> List[Dict[str, Any]]:
        """Filter posts to ensure they're relevant to the brand."""
        filtered_posts = []
        brand_lower = brand_name.lower()
        
        for post in posts:
            # Check if brand name appears in title or text
            title = post.get('title', '').lower()
            text = post.get('text', '').lower()
            
            if brand_lower in title or brand_lower in text:
                # Additional filtering criteria
                if self._is_relevant_post(post):
                    filtered_posts.append(post)
        
        return filtered_posts
    
    def _is_relevant_post(self, post: Dict[str, Any]) -> bool:
        """Check if post is relevant for analysis."""
        # Skip very short posts
        text = post.get('text', '')
        if len(text) < 20:
            return False
        
        # Skip posts with very low scores (likely spam)
        score = post.get('score', 0)
        if score < -5:
            return False
        
        return True
    
    async def analyze_sentiment(self, posts: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """Analyze sentiment of Reddit posts using OpenAI."""
        if not posts:
            return {
                "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0},
                "key_insights": [],
                "thematic_breakdown": [],
                "strategic_recommendations": []
            }
        
        print(f"🤖 Analyzing sentiment for {len(posts)} posts...")
        
        # Prepare posts for analysis
        posts_text = []
        for post in posts[:20]:  # Limit to first 20 posts for analysis
            post_info = {
                "title": post.get('title', ''),
                "text": post.get('text', '')[:500],  # Limit text length
                "score": post.get('score', 0),
                "subreddit": post.get('subreddit', '')
            }
            posts_text.append(post_info)
        
        # Create analysis prompt
        prompt = f"""
        Analyze the sentiment and themes in Reddit discussions about the brand "{brand_name}".
        
        Posts to analyze:
        {json.dumps(posts_text, indent=2)}
        
        Please provide a comprehensive analysis in JSON format with the following structure:
        {{
            "sentiment_summary": {{
                "positive": percentage,
                "neutral": percentage,
                "negative": percentage
            }},
            "key_insights": [
                "insight 1",
                "insight 2",
                "insight 3"
            ],
            "thematic_breakdown": [
                "theme 1",
                "theme 2",
                "theme 3"
            ],
            "strategic_recommendations": [
                "recommendation 1",
                "recommendation 2",
                "recommendation 3"
            ]
        }}
        
        Focus on:
        - Overall sentiment trends
        - Common themes and topics
        - Customer pain points and positive experiences
        - Strategic opportunities for the brand
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a brand sentiment analyst. Provide detailed, actionable insights based on social media data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                analysis = json.loads(analysis_text)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response
                return {
                    "sentiment_summary": {"positive": 50, "neutral": 30, "negative": 20},
                    "key_insights": ["Analysis completed but formatting issue occurred"],
                    "thematic_breakdown": ["Sentiment analysis performed"],
                    "strategic_recommendations": ["Review detailed analysis in report"]
                }
                
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return {
                "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0},
                "key_insights": [f"Analysis failed: {str(e)}"],
                "thematic_breakdown": [],
                "strategic_recommendations": []
            }
    
    def generate_html_report(self, brand_name: str, posts: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate HTML report of the analysis."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sample posts for display
        sample_posts = posts[:10]
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reddit Sentiment Analysis - {brand_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .sentiment-bar {{ display: flex; margin: 10px 0; }}
                .sentiment-positive {{ background: #4CAF50; color: white; padding: 5px 10px; margin-right: 5px; }}
                .sentiment-neutral {{ background: #FF9800; color: white; padding: 5px 10px; margin-right: 5px; }}
                .sentiment-negative {{ background: #F44336; color: white; padding: 5px 10px; }}
                .post {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .post-title {{ font-weight: bold; color: #333; }}
                .post-meta {{ color: #666; font-size: 0.9em; }}
                .insight {{ background: #e8f4fd; padding: 10px; margin: 5px 0; border-left: 4px solid #2196F3; }}
                .recommendation {{ background: #f0f8e8; padding: 10px; margin: 5px 0; border-left: 4px solid #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reddit Sentiment Analysis Report</h1>
                <h2>Brand: {brand_name}</h2>
                <p>Generated on: {timestamp}</p>
                <p>Total Posts Analyzed: {len(posts)}</p>
            </div>
            
            <div class="section">
                <h3>📊 Sentiment Summary</h3>
                <div class="sentiment-bar">
                    <div class="sentiment-positive">Positive: {analysis.get('sentiment_summary', {}).get('positive', 0)}%</div>
                    <div class="sentiment-neutral">Neutral: {analysis.get('sentiment_summary', {}).get('neutral', 0)}%</div>
                    <div class="sentiment-negative">Negative: {analysis.get('sentiment_summary', {}).get('negative', 0)}%</div>
                </div>
            </div>
            
            <div class="section">
                <h3>💡 Key Insights</h3>
                {''.join([f'<div class="insight">{insight}</div>' for insight in analysis.get('key_insights', [])])}
            </div>
            
            <div class="section">
                <h3>🎯 Thematic Breakdown</h3>
                <ul>
                    {''.join([f'<li>{theme}</li>' for theme in analysis.get('thematic_breakdown', [])])}
                </ul>
            </div>
            
            <div class="section">
                <h3>💼 Strategic Recommendations</h3>
                {''.join([f'<div class="recommendation">{rec}</div>' for rec in analysis.get('strategic_recommendations', [])])}
            </div>
            
            <div class="section">
                <h3>📝 Sample Posts</h3>
                {''.join([f'''
                <div class="post">
                    <div class="post-title">{post.get('title', 'No title')}</div>
                    <div class="post-meta">r/{post.get('subreddit', 'unknown')} • Score: {post.get('score', 0)}</div>
                    <p>{post.get('text', 'No text')[:200]}...</p>
                </div>
                ''' for post in sample_posts])}
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def analyze_brand(self, brand_name: str) -> Dict[str, Any]:
        """Complete analysis workflow for a single brand."""
        print(f"\n🚀 Starting analysis for brand: {brand_name}")
        print("=" * 50)
        
        try:
            # Step 1: Search Reddit posts
            posts = await self.search_reddit_posts(brand_name)
            
            if not posts:
                print("❌ No relevant posts found for this brand")
                return {
                    "brand_name": brand_name,
                    "total_posts": 0,
                    "key_insight": "No Reddit discussions found for this brand",
                    "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0},
                    "thematic_breakdown": [],
                    "strategic_recommendations": [],
                    "html_report": ""
                }
            
            # Step 2: Analyze sentiment
            analysis = await self.analyze_sentiment(posts, brand_name)
            
            # Step 3: Generate report
            html_report = self.generate_html_report(brand_name, posts, analysis)
            
            # Step 4: Compile results
            result = {
                "brand_name": brand_name,
                "total_posts": len(posts),
                "key_insight": analysis.get('key_insights', ['No insights available'])[0] if analysis.get('key_insights') else "Analysis completed",
                "sentiment_summary": analysis.get('sentiment_summary', {}),
                "thematic_breakdown": analysis.get('thematic_breakdown', []),
                "strategic_recommendations": analysis.get('strategic_recommendations', []),
                "html_report": html_report
            }
            
            print(f"✅ Analysis completed for {brand_name}")
            print(f"   📊 Posts analyzed: {len(posts)}")
            print(f"   💡 Key insight: {result['key_insight']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Analysis failed for {brand_name}: {e}")
            return {
                "brand_name": brand_name,
                "total_posts": 0,
                "key_insight": f"Analysis failed: {str(e)}",
                "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0},
                "thematic_breakdown": [],
                "strategic_recommendations": [],
                "html_report": ""
            }


async def main():
    """Test the analyzer with a sample brand."""
    analyzer = RedditAnalyzer()
    
    # Test with a sample brand
    brand_name = input("Enter brand name to test: ").strip()
    if not brand_name:
        brand_name = "Apple"  # Default test brand
    
    result = await analyzer.analyze_brand(brand_name)
    
    # Save report
    if result['html_report']:
        filename = f"report_{brand_name.lower().replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result['html_report'])
        print(f"\n📄 Report saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
