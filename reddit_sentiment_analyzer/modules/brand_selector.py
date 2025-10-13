"""
Module 1: Brand Selection
Handles brand selection and prospect management
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from database.db import Database
from typing import Optional, List, Dict, Any
from utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class BrandSelector:
    def __init__(self):
        self.db = Database()
    
    async def get_or_create_prospect(self, brand_name: str) -> Dict[str, Any]:
        """Get existing prospect or create new one"""
        # Check if exists
        prospect = await self.db.get_prospect_by_name(brand_name)
        
        if prospect:
            console.print(f"[green]Found existing prospect: {brand_name}[/green]")
            self._display_prospect_info(prospect)
            return prospect
        
        # Create new prospect
        console.print(f"[yellow]Creating new prospect: {brand_name}[/yellow]")
        prospect_data = self._collect_prospect_info(brand_name)
        prospect = await self.db.create_prospect(prospect_data)
        
        console.print(f"[green]✓ Created new prospect[/green]")
        return prospect
    
    async def get_all_prospects(self) -> List[Dict[str, Any]]:
        """Get all prospects and let user confirm"""
        prospects = await self.db.get_all_prospects()
        
        # Display table
        table = Table(title="All Prospects")
        table.add_column("Brand Name", style="cyan")
        table.add_column("Industry", style="magenta")
        table.add_column("Revenue Range", style="green")
        
        for p in prospects:
            table.add_row(
                p['brand_name'],
                p.get('industry_category', 'N/A'),
                p.get('est_revenue_range', 'N/A')
            )
        
        console.print(table)
        return prospects
    
    def _display_prospect_info(self, prospect: Dict[str, Any]):
        """Display prospect information"""
        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Prospect ID", prospect['id'])
        table.add_row("Brand Name", prospect['brand_name'])
        table.add_row("Industry", prospect.get('industry_category', 'N/A'))
        table.add_row("Revenue Range", prospect.get('est_revenue_range', 'N/A'))
        
        console.print(table)
    
    def _collect_prospect_info(self, brand_name: str) -> Dict[str, Any]:
        """Collect prospect information from user"""
        return {
            'brand_name': brand_name,
            'hq_location': Prompt.ask("HQ Location", default="Unknown"),
            'industry_category': Prompt.ask("Industry Category", default="Wellness"),
            'est_revenue_range': Prompt.ask("Revenue Range", default="$1M-$10M"),
            'website': Prompt.ask("Website", default=""),
            'linkedin_url': Prompt.ask("LinkedIn URL", default=""),
            'why_good_fit': Prompt.ask("Why good fit?", default="DTC wellness brand in target range")
        }

