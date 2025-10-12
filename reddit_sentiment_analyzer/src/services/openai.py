"""
OpenAI service for AI-powered sentiment analysis and report generation.

This service handles interactions with OpenAI's GPT models to perform
comprehensive sentiment analysis and generate strategic insights.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import re

import openai
from openai import AsyncOpenAI

from ..utils.logging import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI's GPT models.
    
    Handles sentiment analysis, insight generation, and comprehensive
    brand intelligence report creation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-latest"):
        """Initialize the OpenAI service."""
        self.settings = get_settings()
        self.api_key = api_key or self.settings.openai_api_key
        self.model = model
        self.client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service and create OpenAI client."""
        if self._initialized:
            return
        
        logger.info("Initializing OpenAI service")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Create OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        self._initialized = True
        logger.info("OpenAI service initialized successfully")
    
    async def analyze_sentiment(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis using GPT-4.
        
        Args:
            analysis_data: Dictionary containing brand info and Reddit posts
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Starting sentiment analysis for brand: {analysis_data.get('brand', 'Unknown')}")
        
        try:
            # Generate the analysis prompt
            prompt = self._generate_analysis_prompt(analysis_data)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a consumer insight strategist. Your job is to analyze Reddit posts about a specific brand and extract strategic intelligence. Your goal is not just to summarize sentiment, but to uncover themes, identify growth opportunities, detect customer confusion, map customer journeys, and suggest actionable tests. Be strategic and structured. You are writing a report for the brand's CMO and Head of Product."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Extract and parse the response
            content = response.choices[0].message.content
            parsed_result = self._parse_analysis_response(content, analysis_data.get('brand', 'Brand'))
            
            logger.info("Sentiment analysis completed successfully")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {e}")
            raise
    
    def _generate_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Generate the analysis prompt for OpenAI."""
        brand = analysis_data.get('brand', 'Brand')
        category = analysis_data.get('category', '')
        company_url = analysis_data.get('company_url', '')
        posts = analysis_data.get('posts', [])
        
        # Limit posts to prevent token overflow
        max_posts = 120
        max_text_length = 1200
        
        # Prepare posts data
        posts_data = []
        for post in posts[:max_posts]:
            post_data = {
                'id': post.get('id', ''),
                'text': str(post.get('text', ''))[:max_text_length],
                'subreddit': post.get('subreddit', ''),
                'createdAt': post.get('createdAt', ''),
                'upVotes': post.get('upVotes', 0),
                'url': post.get('url', ''),
                'brandName': post.get('brandName', brand)
            }
            posts_data.append(post_data)
        
        posts_string = json.dumps(posts_data, indent=2)
        
        prompt = f"""Analyze the Reddit posts/comments about {brand} and create a comprehensive Brand Intelligence Report as a visual HTML artifact using CROSS-DOMAIN PATTERN RECOGNITION.

You are an expert in behavioral science, cultural anthropology, and AI-powered consumer psychology. Apply these lenses to find hidden patterns others miss.

DATA (array of posts):
{posts_string}

KEY INSIGHT GENERATION RULES:
Your KEY_INSIGHT must follow this formula: [Brand] faces a "[specific behavioral/psychological phenomenon]" - [specific percentage] of [specific behavior], [cross-domain framework explains why], particularly [specific audience segment].

Examples:
- "Seed Health faces a 'scientific skepticism paradox' - while 28% of discussions are positive, growing evidence-based criticism of probiotics is creating doubt among educated health enthusiasts, particularly post-antibiotic users seeking alternatives"
- "Brand X exhibits 'social proof cascade failure' - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation"

HTML STRUCTURE REQUIREMENTS - Follow this EXACT format:

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brand Intelligence Report - {brand}</title>
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
        .insight-box {{ background: #FFD700; color: #000; padding: 15px; margin: 15px 0; font-weight: bold; }}
        .key-insight {{ background: #000; color: #FFD700; padding: 20px; margin: 20px 0; font-size: 1.2em; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #FFD700; color: #000; font-weight: bold; }}
        .segment-boxes {{ display: flex; gap: 15px; margin: 15px 0; }}
        .segment-box {{ background: #FFD700; color: #000; padding: 15px; flex: 1; }}
        .finding-box {{ background: #FFD700; color: #000; padding: 15px; margin: 15px 0; }}
        .journey-badges {{ display: flex; gap: 10px; margin: 15px 0; }}
        .journey-badge {{ padding: 8px 15px; border-radius: 20px; font-size: 0.9em; }}
        .consideration {{ background: #3498db; color: white; }}
        .experience {{ background: #f39c12; color: white; }}
        .advocacy {{ background: #2ecc71; color: white; }}
        .churn {{ background: #e74c3c; color: white; }}
        .recommendations {{ display: grid; grid-template-columns: 1fr; gap: 15px; }}
        .rec-section {{ background: #f8f9fa; padding: 15px; border-left: 3px solid #FFD700; }}
        .test-box {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 3px solid #FFD700; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BRAND INTELLIGENCE REPORT</h1>
        <h2>{brand.upper()} - Reddit Consumer Intelligence Analysis</h2>
        <p>Total Analyzed: [X] Posts & Comments | Analysis Period: Recent Reddit Activity</p>
    </div>

    <div class="section">
        <div class="section-title">EXECUTIVE SUMMARY</div>
        <div class="key-insight">
            KEY INSIGHT: [Your cross-domain behavioral insight here following the formula]
        </div>
    </div>

    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">[X]</div>
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
        <div class="section-title">Sentiment Distribution</div>
        [Include pie chart or visual representation]
        <div class="insight-box">
            Insight: [Behavioral science interpretation of sentiment pattern]
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
        <div class="segment-boxes">
            [3 customer segment boxes with behavioral descriptions]
        </div>
        <div class="finding-box">
            Surprising Finding: [Cross-domain insight about unexpected audience or behavior]
        </div>
    </div>

    <div class="section">
        <div class="section-title">Customer Journey Stage Signals</div>
        <div class="journey-badges">
            <span class="journey-badge consideration">Consideration: [X] mentions</span>
            <span class="journey-badge experience">Experience: [X] mentions</span>
            <span class="journey-badge advocacy">Advocacy: [X] mentions</span>
            <span class="journey-badge churn">Churn: [X] mentions</span>
        </div>
        <div class="insight-box">
            Journey Insight: [Behavioral analysis of customer journey patterns]
        </div>
    </div>

    <div class="section">
        <div class="section-title">Competitor Intelligence</div>
        <table>
            <tr><th>Competitor</th><th>Mentions</th><th>Context</th><th>Threat Level</th></tr>
            [Competitor analysis rows]
        </table>
        <div class="insight-box">
            Competitive Insight: [Cross-domain analysis of competitive threats]
        </div>
    </div>

    <div class="section">
        <div class="section-title">Confusion & Pain Points</div>
        [List of specific pain points and confusions]
        <div class="insight-box">
            Core Confusion: [Behavioral psychology explanation of root confusion]
        </div>
    </div>

    <div class="section">
        <div class="section-title">Strategic Recommendations</div>
        <div class="recommendations">
            <div class="rec-section">
                <h4>A. Content & Messaging Strategy</h4>
                [Specific recommendations based on behavioral insights]
            </div>
            <div class="rec-section">
                <h4>B. Product/UX Improvements</h4>
                [Product recommendations based on psychological patterns]
            </div>
            <div class="rec-section">
                <h4>C. Growth Opportunities</h4>
                [Growth strategies based on cultural/anthropological insights]
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Hypothesis-Driven Tests</div>
        <div class="test-box">
            <h4>Test 1: [Specific behavioral test]</h4>
            <p><strong>Hypothesis:</strong> [Behavioral science hypothesis]</p>
            <p><strong>Success Metric:</strong> [Specific measurable outcome]</p>
        </div>
        <div class="test-box">
            <h4>Test 2: [Second behavioral test]</h4>
            <p><strong>Hypothesis:</strong> [Second hypothesis]</p>
            <p><strong>Success Metric:</strong> [Second metric]</p>
        </div>
        <div class="test-box">
            <h4>Test 3: [Third behavioral test]</h4>
            <p><strong>Hypothesis:</strong> [Third hypothesis]</p>
            <p><strong>Success Metric:</strong> [Third metric]</p>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Bottom Line Intelligence</div>
        <h4>Executive Summary</h4>
        <p><strong>The Challenge:</strong> [Core behavioral/psychological challenge]</p>
        <p><strong>The Opportunity:</strong> [Strategic opportunity based on cross-domain insights]</p>
        <p><strong>Priority Actions:</strong> [3 specific actionable recommendations]</p>
    </div>

    <div class="section">
        <div class="section-title">Limitations</div>
        <p><strong>Sample Bias:</strong> [Specific bias explanation]</p>
        <p><strong>Platform Bias:</strong> [Reddit-specific limitations]</p>
        <p><strong>Temporal Bias:</strong> [Time-based limitations]</p>
        <p><strong>Volume Limitation:</strong> [Sample size considerations]</p>
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
{brand}
</BRAND_NAME>
<KEY_INSIGHT>
[Brand] faces a "[behavioral phenomenon]" - [percentage] of [specific behavior], [cross-domain explanation], particularly [audience segment]
</KEY_INSIGHT>
<HTML_REPORT>
[Complete HTML following the exact structure above]
</HTML_REPORT>"""
        
        return prompt
    
    def _parse_analysis_response(self, content: str, brand_name: str) -> Dict[str, Any]:
        """Parse the OpenAI response and extract structured data."""
        try:
            # Extract brand name
            brand_match = re.search(r'<BRAND_NAME>\s*(.*?)\s*</BRAND_NAME>', content, re.DOTALL)
            extracted_brand = brand_match.group(1).strip() if brand_match else brand_name
            
            # Extract key insight
            insight_match = re.search(r'<KEY_INSIGHT>\s*(.*?)\s*</KEY_INSIGHT>', content, re.DOTALL)
            key_insight = insight_match.group(1).strip() if insight_match else "No key insight found"
            
            # Extract HTML report
            html_match = re.search(r'<HTML_REPORT>\s*(.*?)\s*</HTML_REPORT>', content, re.DOTALL)
            html_report = html_match.group(1).strip() if html_match else ""
            
            # Parse sentiment summary from HTML (basic extraction)
            sentiment_summary = self._extract_sentiment_from_html(html_report)
            
            # Extract thematic breakdown
            thematic_breakdown = self._extract_thematic_breakdown(html_report)
            
            # Extract customer segments
            customer_segments = self._extract_customer_segments(html_report)
            
            # Extract strategic recommendations
            strategic_recommendations = self._extract_strategic_recommendations(html_report)
            
            return {
                "brand_name": extracted_brand,
                "key_insight": key_insight,
                "html_report": html_report,
                "sentiment_summary": sentiment_summary,
                "thematic_breakdown": thematic_breakdown,
                "customer_segments": customer_segments,
                "strategic_recommendations": strategic_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            # Return fallback structure
            return {
                "brand_name": brand_name,
                "key_insight": "Analysis completed but parsing failed",
                "html_report": content,
                "sentiment_summary": {"positive": 0, "negative": 0, "neutral": 0},
                "thematic_breakdown": [],
                "customer_segments": [],
                "strategic_recommendations": []
            }
    
    def _extract_sentiment_from_html(self, html_content: str) -> Dict[str, int]:
        """Extract sentiment summary from HTML content."""
        # This is a basic extraction - in production, you might want more sophisticated parsing
        sentiment_summary = {"positive": 0, "negative": 0, "neutral": 0}
        
        # Look for percentage patterns in the HTML
        positive_match = re.search(r'POSITIVE.*?(\d+)%', html_content)
        negative_match = re.search(r'NEGATIVE.*?(\d+)%', html_content)
        neutral_match = re.search(r'NEUTRAL.*?(\d+)%', html_content)
        
        if positive_match:
            sentiment_summary["positive"] = int(positive_match.group(1))
        if negative_match:
            sentiment_summary["negative"] = int(negative_match.group(1))
        if neutral_match:
            sentiment_summary["neutral"] = int(neutral_match.group(1))
        
        return sentiment_summary
    
    def _extract_thematic_breakdown(self, html_content: str) -> List[str]:
        """Extract thematic breakdown from HTML content."""
        # Basic extraction - look for table rows or list items
        themes = []
        
        # Look for table rows in thematic breakdown section
        table_match = re.search(r'<table>.*?</table>', html_content, re.DOTALL)
        if table_match:
            # Extract table content (simplified)
            themes.append("Thematic analysis available in HTML report")
        
        return themes
    
    def _extract_customer_segments(self, html_content: str) -> List[str]:
        """Extract customer segments from HTML content."""
        segments = []
        
        # Look for segment boxes
        segment_matches = re.findall(r'<div class="segment-box">(.*?)</div>', html_content, re.DOTALL)
        for match in segment_matches:
            # Clean up HTML tags
            clean_text = re.sub(r'<[^>]+>', '', match).strip()
            if clean_text:
                segments.append(clean_text)
        
        return segments
    
    def _extract_strategic_recommendations(self, html_content: str) -> List[str]:
        """Extract strategic recommendations from HTML content."""
        recommendations = []
        
        # Look for recommendation sections
        rec_matches = re.findall(r'<div class="rec-section">.*?<h4>(.*?)</h4>.*?</div>', html_content, re.DOTALL)
        for match in rec_matches:
            # Clean up HTML tags
            clean_text = re.sub(r'<[^>]+>', '', match).strip()
            if clean_text:
                recommendations.append(clean_text)
        
        return recommendations
    
    async def test_connection(self) -> bool:
        """
        Test connection to OpenAI API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Make a simple test request
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            
            logger.info("Successfully connected to OpenAI API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            return False
    
    async def close(self) -> None:
        """Close the service and clean up resources."""
        logger.info("Closing OpenAI service")
        self.client = None
        self._initialized = False
