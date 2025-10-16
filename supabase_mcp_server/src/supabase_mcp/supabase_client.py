"""
Supabase client wrapper for MCP server
"""

from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from .config import get_settings


class SupabaseClient:
    """Wrapper for Supabase client with common operations"""

    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)

    def _get_table(self, table_name: str):
        """Get table reference, handling schema-qualified names"""
        if '.' in table_name:
            schema, table = table_name.split('.', 1)
            return self.client.schema(schema).table(table)
        return self.client.table(table_name)
    
    async def query_table(
        self,
        table_name: str,
        select: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query a table with optional filters"""
        query = self._get_table(table_name).select(select)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data
    
    async def insert_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a table"""
        response = self._get_table(table_name).insert(data).execute()
        return response.data[0] if response.data else {}
    
    async def update_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Update data in a table"""
        query = self._get_table(table_name).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        response = query.execute()
        return response.data
    
    async def delete_data(self, table_name: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Delete data from a table"""
        query = self._get_table(table_name).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        response = query.execute()
        return response.data
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        # This would require additional Supabase admin API calls
        # For now, return basic info
        return {"table_name": table_name, "note": "Schema info requires admin API"}
