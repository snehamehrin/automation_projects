"""
Supabase service for database operations.

This service handles all interactions with Supabase including
authentication, reading brand data, and writing analysis results.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from supabase import create_client, Client

from ..data.models import BrandData, AnalysisResult
from ..utils.logging import get_logger
from ..config.settings import get_supabase_settings

logger = get_logger(__name__)


class SupabaseService:
    """
    Service for interacting with Supabase database.
    
    Handles authentication, reading brand data, and writing analysis results
    to Supabase tables.
    """
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """Initialize the Supabase service."""
        self.settings = get_supabase_settings()
        self.url = url or self.settings.url
        self.key = key or self.settings.key
        self.client: Optional[Client] = None
        self._authenticated = False
    
    async def initialize(self) -> None:
        """Initialize the service and authenticate with Supabase."""
        if self._authenticated:
            return
        
        logger.info("Initializing Supabase service")
        
        try:
            if not self.url or not self.key:
                raise ValueError("Supabase URL and key are required")
            
            # Create Supabase client
            self.client = create_client(self.url, self.key)
            
            # Test connection
            await self._test_connection()
            
            self._authenticated = True
            logger.info("Supabase service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase service: {e}")
            raise
    
    async def _test_connection(self) -> None:
        """Test connection to Supabase."""
        try:
            # Try to query a simple table to test connection
            result = self.client.table("brands").select("id").limit(1).execute()
            logger.debug("Supabase connection test successful")
        except Exception as e:
            logger.warning(f"Supabase connection test failed: {e}")
            # Don't raise error as table might not exist yet
    
    async def load_brands(self) -> List[BrandData]:
        """
        Load brand data from Supabase brands table.
        
        Returns:
            List of BrandData objects
        """
        if not self._authenticated:
            await self.initialize()
        
        logger.info("Loading brands from Supabase")
        
        try:
            # Query brands table
            result = self.client.table(self.settings.brands_table).select("*").execute()
            
            brands = []
            for row in result.data:
                try:
                    brand = BrandData(
                        name=row.get('name', ''),
                        category=row.get('category'),
                        company_url=row.get('company_url')
                    )
                    if brand.name:  # Only add non-empty brand names
                        brands.append(brand)
                except Exception as e:
                    logger.warning(f"Failed to parse brand row: {e}")
                    continue
            
            logger.info(f"Loaded {len(brands)} brands from Supabase")
            return brands
            
        except Exception as e:
            logger.error(f"Error loading brands from Supabase: {e}")
            raise
    
    async def save_analysis_results(self, results: List[AnalysisResult]) -> None:
        """
        Save analysis results to Supabase results table.
        
        Args:
            results: List of analysis results to save
        """
        if not self._authenticated:
            await self.initialize()
        
        if not results:
            logger.warning("No results to save")
            return
        
        logger.info(f"Saving {len(results)} analysis results to Supabase")
        
        try:
            # Prepare data for insertion
            data_to_insert = []
            for result in results:
                data = {
                    'brand_name': result.brand_name,
                    'brand_category': result.brand_category,
                    'company_url': result.company_url,
                    'analysis_timestamp': result.analysis_timestamp.isoformat(),
                    'total_posts': result.total_posts,
                    'key_insight': result.key_insight,
                    'sentiment_summary': result.sentiment_summary,
                    'thematic_breakdown': result.thematic_breakdown,
                    'customer_segments': result.customer_segments,
                    'strategic_recommendations': result.strategic_recommendations,
                    'html_report': result.html_report,
                    'created_at': datetime.utcnow().isoformat()
                }
                data_to_insert.append(data)
            
            # Insert data into results table
            result = self.client.table(self.settings.results_table).insert(data_to_insert).execute()
            
            logger.info(f"Successfully saved {len(results)} results to Supabase")
            
        except Exception as e:
            logger.error(f"Error saving results to Supabase: {e}")
            raise
    
    async def add_brand(self, brand_data: BrandData) -> Dict[str, Any]:
        """
        Add a new brand to the brands table.
        
        Args:
            brand_data: Brand data to add
            
        Returns:
            Inserted brand data
        """
        if not self._authenticated:
            await self.initialize()
        
        logger.info(f"Adding brand to Supabase: {brand_data.name}")
        
        try:
            data = {
                'name': brand_data.name,
                'category': brand_data.category,
                'company_url': brand_data.company_url,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table(self.settings.brands_table).insert(data).execute()
            
            logger.info(f"Successfully added brand: {brand_data.name}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error adding brand to Supabase: {e}")
            raise
    
    async def get_analysis_results(self, brand_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get analysis results from Supabase.
        
        Args:
            brand_name: Optional brand name to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of analysis results
        """
        if not self._authenticated:
            await self.initialize()
        
        logger.info("Loading analysis results from Supabase")
        
        try:
            query = self.client.table(self.settings.results_table).select("*")
            
            if brand_name:
                query = query.eq('brand_name', brand_name)
            
            query = query.order('created_at', desc=True).limit(limit)
            result = query.execute()
            
            logger.info(f"Loaded {len(result.data)} analysis results from Supabase")
            return result.data
            
        except Exception as e:
            logger.error(f"Error loading analysis results from Supabase: {e}")
            raise
    
    async def create_tables(self) -> None:
        """
        Create necessary tables in Supabase if they don't exist.
        This is a helper method - in production, you'd use Supabase migrations.
        """
        logger.info("Creating tables in Supabase (if they don't exist)")
        
        # Note: In a real implementation, you'd use Supabase migrations
        # This is just a placeholder for the table structure
        table_schemas = {
            'brands': {
                'id': 'bigserial primary key',
                'name': 'text not null',
                'category': 'text',
                'company_url': 'text',
                'created_at': 'timestamp with time zone default now()'
            },
            'analysis_results': {
                'id': 'bigserial primary key',
                'brand_name': 'text not null',
                'brand_category': 'text',
                'company_url': 'text',
                'analysis_timestamp': 'timestamp with time zone',
                'total_posts': 'integer',
                'key_insight': 'text',
                'sentiment_summary': 'jsonb',
                'thematic_breakdown': 'jsonb',
                'customer_segments': 'jsonb',
                'strategic_recommendations': 'jsonb',
                'html_report': 'text',
                'created_at': 'timestamp with time zone default now()'
            }
        }
        
        logger.info("Table schemas defined (use Supabase migrations to create tables)")
        logger.info(f"Brands table schema: {table_schemas['brands']}")
        logger.info(f"Analysis results table schema: {table_schemas['analysis_results']}")
    
    async def test_connection(self) -> bool:
        """
        Test connection to Supabase.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._authenticated:
                await self.initialize()
            
            # Try to query a simple table
            result = self.client.table(self.settings.brands_table).select("id").limit(1).execute()
            
            logger.info("Successfully connected to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    async def close(self) -> None:
        """Close the service and clean up resources."""
        logger.info("Closing Supabase service")
        self.client = None
        self._authenticated = False
