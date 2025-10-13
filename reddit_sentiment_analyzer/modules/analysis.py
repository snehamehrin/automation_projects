"""
Module 5: ChatGPT Analysis
Generates brand intelligence reports using OpenAI
"""

import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from config.settings import get_settings
from database.db import Database
from utils.logger import get_logger
from datetime import datetime

settings = get_settings()
logger = get_logger(__name__)


class Analyzer:
    def __init__(self):
        self.db = Database()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def analyze(
        self, 
        posts: List[Dict[str, Any]], 
        brand_name: str, 
        prospect_id: str
    ) -> Dict[str, Any]:
        """Run ChatGPT analysis on cleaned posts"""
        logger.info(f"Analyzing {len(posts)} posts for {brand_name}")
        
        # Limit posts
        posts = posts[:120]
        
        # Generate prompt
        prompt = self._generate_prompt(posts, brand_name)
        
        # Call ChatGPT
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a consumer insight strategist analyzing Reddit posts about brands. Extract strategic intelligence, identify growth opportunities, detect customer confusion, map customer journeys, and suggest actionable tests."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=16000
        )
        
        # Extract response
        raw_content = response.choices[0].message.content
        
        # Parse structured output
        parsed = self._parse_response(raw_content, brand_name, prospect_id)
        
        # Store in database
        await self.db.insert_analysis_result(parsed)
        
        logger.info(f"Analysis complete for {brand_name}")
        return parsed
    
    def _generate_prompt(self, posts: List[Dict[str, Any]], brand_name: str) -> str:
        """Generate ChatGPT prompt"""
        posts_json = json.dumps(posts, indent=2)[:180000]  # Limit size
        
        return f"""Analyze the Reddit posts/comments about {brand_name} and create a comprehensive Brand Intelligence Report as a visual HTML artifact using CROSS-DOMAIN PATTERN RECOGNITION.

You are an expert in behavioral science, cultural anthropology, and AI-powered consumer psychology. Apply these lenses to find hidden patterns others miss.

DATA (array of posts):
{posts_json}

KEY INSIGHT GENERATION RULES:
Your KEY_INSIGHT must follow this formula: [Brand] faces a "[specific behavioral/psychological phenomenon]" - [specific percentage] of [specific behavior], [cross-domain framework explains why], particularly [specific audience segment].

Examples:
- "Seed Health faces a 'scientific skepticism paradox' - while 28% of discussions are positive, growing evidence-based criticism of probiotics is creating doubt among educated health enthusiasts, particularly post-antibiotic users seeking alternatives"
- "Brand X exhibits 'social proof cascade failure' - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation"

OUTPUT FORMAT:
You must output in this exact structure:

<BRAND_NAME>
{brand_name}
</BRAND_NAME>

<KEY_INSIGHT>
[Your behavioral insight following the formula above]
</KEY_INSIGHT>

<HTML_REPORT>
[Complete HTML report following the template structure with proper sections, styling, and insights]
</HTML_REPORT>

The HTML report should include:
1. Executive Summary with key insight
2. Sentiment Distribution with stats
3. Thematic Breakdown
4. Customer Segment Analysis
5. Customer Journey Signals
6. Competitor Intelligence
7. Pain Points & Confusions
8. Strategic Recommendations
9. Hypothesis-Driven Tests
10. Bottom Line Intelligence
11. Limitations

Use behavioral science, anthropology, and economic frameworks to provide deep insights."""
    
    def _parse_response(
        self, 
        raw_content: str, 
        brand_name: str, 
        prospect_id: str
    ) -> Dict[str, Any]:
        """Parse structured response from ChatGPT"""
        # Extract sections
        brand_match = self._extract_section(raw_content, 'BRAND_NAME')
        insight_match = self._extract_section(raw_content, 'KEY_INSIGHT')
        html_match = self._extract_section(raw_content, 'HTML_REPORT')
        
        return {
            'brand_name': brand_match or brand_name,
            'key_insight': insight_match or 'Analysis complete',
            'html_content': html_match or raw_content,
            'analysis_date': datetime.utcnow().isoformat(),
            'prospect_id': prospect_id
        }
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content between XML-style tags"""
        start_tag = f"<{section_name}>"
        end_tag = f"</{section_name}>"
        
        start_idx = content.find(start_tag)
        if start_idx == -1:
            return ""
        
        start_idx += len(start_tag)
        end_idx = content.find(end_tag, start_idx)
        
        if end_idx == -1:
            return ""
        
        return content[start_idx:end_idx].strip()

