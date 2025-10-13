"""
Test script for brand selector module
"""

import asyncio
from modules.brand_selector import BrandSelector

async def test():
    """Test brand selector functionality"""
    selector = BrandSelector()
    
    # Test getting or creating a prospect
    prospect = await selector.get_or_create_prospect("Seed Health")
    print(f"Prospect: {prospect}")
    
    # Test getting all prospects
    prospects = await selector.get_all_prospects()
    print(f"Total prospects: {len(prospects)}")

if __name__ == "__main__":
    asyncio.run(test())

