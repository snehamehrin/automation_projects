"""
Main analyzer orchestrator for the Reddit sentiment analysis workflow.

This module implements the core business logic that coordinates all components
of the sentiment analysis pipeline, following the N8N workflow structure.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..services.supabase import SupabaseService
from ..services.apify import ApifyService
from ..services.openai import OpenAIService
from ..data.models import BrandData, AnalysisResult, RedditPost
from ..data.processors import DataProcessor
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RedditSentimentAnalyzer:
    """
    Main orchestrator for the Reddit sentiment analysis workflow.
    
    This class coordinates the entire analysis pipeline:
    1. Data input (Google Sheets or manual)
    2. Search and scraping (Google Search + Reddit)
    3. Data processing and filtering
    4. AI analysis and report generation
    5. Output (Google Sheets or file)
    """
    
    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        apify_service: Optional[ApifyService] = None,
        openai_service: Optional[OpenAIService] = None,
        data_processor: Optional[DataProcessor] = None,
    ):
        """Initialize the analyzer with service dependencies."""
        self.supabase = supabase_service or SupabaseService()
        self.apify = apify_service or ApifyService()
        self.openai = openai_service or OpenAIService()
        self.data_processor = data_processor or DataProcessor()
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all services and validate configuration."""
        if self._initialized:
            return
            
        logger.info("Initializing Reddit Sentiment Analyzer")
        
        # Initialize services
        await self.supabase.initialize()
        await self.apify.initialize()
        await self.openai.initialize()
        await self.data_processor.initialize()
        
        self._initialized = True
        logger.info("Reddit Sentiment Analyzer initialized successfully")
    
    async def analyze_brand(self, brand_data: BrandData) -> AnalysisResult:
        """
        Analyze sentiment for a single brand.
        
        Args:
            brand_data: Brand information including name, category, and URL
            
        Returns:
            AnalysisResult containing sentiment analysis and insights
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Starting analysis for brand: {brand_data.name}")
        
        try:
            # Step 1: Generate search query
            search_query = self._generate_search_query(brand_data)
            logger.debug(f"Generated search query: {search_query}")
            
            # Step 2: Search for Reddit URLs using Google Search
            reddit_urls = await self._search_reddit_urls(search_query)
            logger.info(f"Found {len(reddit_urls)} Reddit URLs")
            
            # Step 3: Scrape Reddit content
            reddit_posts = await self._scrape_reddit_content(reddit_urls)
            logger.info(f"Scraped {len(reddit_posts)} Reddit posts/comments")
            
            # Step 4: Process and filter data
            processed_posts = await self._process_reddit_data(reddit_posts, brand_data)
            logger.info(f"Processed {len(processed_posts)} posts after filtering")
            
            # Step 5: Generate AI analysis
            analysis_result = await self._generate_ai_analysis(processed_posts, brand_data)
            logger.info("AI analysis completed")
            
            # Step 6: Create final result
            result = AnalysisResult(
                brand_name=brand_data.name,
                brand_category=brand_data.category,
                company_url=brand_data.company_url,
                total_posts=len(processed_posts),
                analysis_timestamp=datetime.utcnow(),
                sentiment_summary=analysis_result.get("sentiment_summary", {}),
                key_insight=analysis_result.get("key_insight", ""),
                thematic_breakdown=analysis_result.get("thematic_breakdown", []),
                customer_segments=analysis_result.get("customer_segments", []),
                strategic_recommendations=analysis_result.get("strategic_recommendations", []),
                html_report=analysis_result.get("html_report", ""),
                raw_data=processed_posts
            )
            
            logger.info(f"Analysis completed for brand: {brand_data.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing brand {brand_data.name}: {e}", exc_info=True)
            raise
    
    async def analyze_brands_batch(self, brands: List[BrandData]) -> List[AnalysisResult]:
        """
        Analyze sentiment for multiple brands in batch.
        
        Args:
            brands: List of brand data to analyze
            
        Returns:
            List of analysis results for each brand
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Starting batch analysis for {len(brands)} brands")
        
        # Process brands concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent analyses
        
        async def analyze_with_semaphore(brand: BrandData) -> AnalysisResult:
            async with semaphore:
                return await self.analyze_brand(brand)
        
        tasks = [analyze_with_semaphore(brand) for brand in brands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze brand {brands[i].name}: {result}")
            else:
                successful_results.append(result)
        
        logger.info(f"Batch analysis completed: {len(successful_results)}/{len(brands)} successful")
        return successful_results
    
    async def analyze_from_supabase(self) -> List[AnalysisResult]:
        """
        Analyze brands from Supabase database.
        
        Returns:
            List of analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info("Loading brands from Supabase")
        
        # Load brand data from Supabase
        brands = await self.supabase.load_brands()
        logger.info(f"Loaded {len(brands)} brands from Supabase")
        
        # Analyze all brands
        results = await self.analyze_brands_batch(brands)
        
        # Save results to Supabase
        if results:
            logger.info("Saving results to Supabase")
            await self.supabase.save_analysis_results(results)
        
        return results
    
    def _generate_search_query(self, brand_data: BrandData) -> str:
        """Generate Google search query for Reddit discussions."""
        base_query = f"site:reddit.com {brand_data.name}"
        
        if brand_data.category:
            base_query += f" {brand_data.category}"
        
        # Add review-related terms
        review_terms = ["review", "reviews", "opinion", "experience", "feedback"]
        query_variants = [f"{base_query} {term}" for term in review_terms]
        
        return " OR ".join(query_variants)
    
    async def _search_reddit_urls(self, search_query: str) -> List[str]:
        """Search for Reddit URLs using Google Search via Apify."""
        logger.debug(f"Searching for Reddit URLs with query: {search_query}")
        
        search_results = await self.apify.google_search(search_query)
        reddit_urls = []
        
        for result in search_results.get("organicResults", []):
            url = result.get("url", "")
            if "reddit.com/r/" in url:
                reddit_urls.append(url)
        
        logger.debug(f"Found {len(reddit_urls)} Reddit URLs")
        return reddit_urls
    
    async def _scrape_reddit_content(self, reddit_urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape Reddit content using Apify Reddit scraper."""
        if not reddit_urls:
            return []
        
        logger.debug(f"Scraping content from {len(reddit_urls)} Reddit URLs")
        
        all_posts = []
        for url in reddit_urls:
            try:
                posts = await self.apify.scrape_reddit(url)
                all_posts.extend(posts)
            except Exception as e:
                logger.warning(f"Failed to scrape Reddit URL {url}: {e}")
        
        logger.debug(f"Scraped {len(all_posts)} total posts/comments")
        return all_posts
    
    async def _process_reddit_data(
        self, 
        raw_posts: List[Dict[str, Any]], 
        brand_data: BrandData
    ) -> List[RedditPost]:
        """Process and filter Reddit data."""
        logger.debug(f"Processing {len(raw_posts)} raw posts")
        
        # Convert to RedditPost objects and add brand context
        posts = []
        for post_data in raw_posts:
            try:
                post = RedditPost.from_dict(post_data)
                post.brand_name = brand_data.name
                post.company_url = brand_data.company_url
                posts.append(post)
            except Exception as e:
                logger.warning(f"Failed to process post: {e}")
        
        # Apply data processing pipeline
        processed_posts = await self.data_processor.process_posts(posts)
        
        logger.debug(f"Processed {len(processed_posts)} posts after filtering")
        return processed_posts
    
    async def _generate_ai_analysis(
        self, 
        posts: List[RedditPost], 
        brand_data: BrandData
    ) -> Dict[str, Any]:
        """Generate AI analysis using OpenAI."""
        logger.debug(f"Generating AI analysis for {len(posts)} posts")
        
        # Prepare data for AI analysis
        analysis_data = {
            "brand": brand_data.name,
            "category": brand_data.category,
            "company_url": brand_data.company_url,
            "posts": [post.to_dict() for post in posts]
        }
        
        # Generate comprehensive analysis
        analysis_result = await self.openai.analyze_sentiment(analysis_data)
        
        logger.debug("AI analysis generation completed")
        return analysis_result
    
    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing Reddit Sentiment Analyzer")
        
        if hasattr(self.supabase, 'close'):
            await self.supabase.close()
        if hasattr(self.apify, 'close'):
            await self.apify.close()
        if hasattr(self.openai, 'close'):
            await self.openai.close()
        
        self._initialized = False
        logger.info("Reddit Sentiment Analyzer closed")
