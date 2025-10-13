"""
Database connection and operations
"""

from supabase import create_client, Client
from config.settings import get_settings
from typing import Optional, List, Dict, Any

settings = get_settings()


class Database:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def get_prospect_by_name(self, brand_name: str) -> Optional[Dict[str, Any]]:
        """Get prospect by brand name"""
        response = self.client.table('prospects').select('*').eq('brand_name', brand_name).execute()
        return response.data[0] if response.data else None
    
    async def create_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new prospect"""
        response = self.client.table('prospects').insert(prospect_data).execute()
        return response.data[0]
    
    async def get_all_prospects(self) -> List[Dict[str, Any]]:
        """Get all prospects"""
        response = self.client.table('prospects').select('*').execute()
        return response.data
    
    async def update_prospect(self, prospect_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update prospect"""
        response = self.client.table('prospects').update(data).eq('id', prospect_id).execute()
        return response.data[0]
    
    async def insert_reddit_urls(self, urls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert Reddit URLs"""
        response = self.client.table('brand_google_reddit').insert(urls).execute()
        return response.data
    
    async def get_reddit_urls(self, prospect_id: str) -> List[Dict[str, Any]]:
        """Get Reddit URLs for prospect"""
        response = self.client.table('brand_google_reddit').select('*').eq('prospect_id', prospect_id).execute()
        return response.data
    
    async def insert_posts_comments(self, data: List[Dict[str, Any]]) -> None:
        """Bulk insert posts and comments"""
        if not data:
            return
        
        # Batch insert in chunks of 1000
        chunk_size = 1000
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.client.table('brand_reddit_posts_comments').insert(chunk).execute()
    
    async def insert_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Insert analysis result"""
        response = self.client.table('reddit_brand_analysis_results').insert(result).execute()
        return response.data[0]
    
    async def mark_urls_processed(self, prospect_id: str, urls: List[str]) -> None:
        """Mark URLs as processed after scraping"""
        for url in urls:
            self.client.table('brand_google_reddit').update({'processed': True}).eq('prospect_id', prospect_id).eq('url', url).execute()

