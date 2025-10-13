"""
Unit tests for brand_selector module
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from modules.brand_selector import BrandSelector


class TestBrandSelector:
    """Test cases for BrandSelector class"""
    
    @pytest.fixture
    def brand_selector(self, mock_database):
        """Create BrandSelector instance with mocked database"""
        with patch('modules.brand_selector.Database', return_value=mock_database):
            return BrandSelector()
    
    @pytest.mark.asyncio
    async def test_get_or_create_prospect_existing(self, brand_selector, mock_database, mock_prospect_data):
        """Test getting existing prospect"""
        # Setup
        mock_database.get_prospect_by_name.return_value = mock_prospect_data
        
        # Execute
        result = await brand_selector.get_or_create_prospect("Test Brand")
        
        # Assert
        assert result == mock_prospect_data
        mock_database.get_prospect_by_name.assert_called_once_with("Test Brand")
        mock_database.create_prospect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_or_create_prospect_new(self, brand_selector, mock_database, mock_prospect_data):
        """Test creating new prospect"""
        # Setup
        mock_database.get_prospect_by_name.return_value = None
        mock_database.create_prospect.return_value = mock_prospect_data
        
        # Mock user input
        with patch('modules.brand_selector.Prompt') as mock_prompt:
            mock_prompt.ask.side_effect = [
                "San Francisco, CA",  # HQ Location
                "Wellness",           # Industry Category
                "$1M-$10M",          # Revenue Range
                "https://testbrand.com",  # Website
                "https://linkedin.com/company/testbrand",  # LinkedIn
                "DTC wellness brand in target range"  # Why good fit
            ]
            
            # Execute
            result = await brand_selector.get_or_create_prospect("Test Brand")
        
        # Assert
        assert result == mock_prospect_data
        mock_database.get_prospect_by_name.assert_called_once_with("Test Brand")
        mock_database.create_prospect.assert_called_once()
        
        # Verify prospect data structure
        call_args = mock_database.create_prospect.call_args[0][0]
        assert call_args['brand_name'] == "Test Brand"
        assert call_args['hq_location'] == "San Francisco, CA"
        assert call_args['industry_category'] == "Wellness"
    
    @pytest.mark.asyncio
    async def test_get_all_prospects(self, brand_selector, mock_database, mock_prospect_data):
        """Test getting all prospects"""
        # Setup
        mock_database.get_all_prospects.return_value = [mock_prospect_data]
        
        # Execute
        result = await brand_selector.get_all_prospects()
        
        # Assert
        assert result == [mock_prospect_data]
        mock_database.get_all_prospects.assert_called_once()
    
    def test_display_prospect_info(self, brand_selector, mock_prospect_data):
        """Test displaying prospect information"""
        # This test verifies the method doesn't raise exceptions
        # In a real test, you might capture console output
        try:
            brand_selector._display_prospect_info(mock_prospect_data)
            assert True  # Method executed without error
        except Exception as e:
            pytest.fail(f"_display_prospect_info raised {e}")
    
    def test_collect_prospect_info(self, brand_selector):
        """Test collecting prospect information from user"""
        with patch('modules.brand_selector.Prompt') as mock_prompt:
            mock_prompt.ask.side_effect = [
                "San Francisco, CA",  # HQ Location
                "Wellness",           # Industry Category
                "$1M-$10M",          # Revenue Range
                "https://testbrand.com",  # Website
                "https://linkedin.com/company/testbrand",  # LinkedIn
                "DTC wellness brand in target range"  # Why good fit
            ]
            
            result = brand_selector._collect_prospect_info("Test Brand")
        
        assert result['brand_name'] == "Test Brand"
        assert result['hq_location'] == "San Francisco, CA"
        assert result['industry_category'] == "Wellness"
        assert result['est_revenue_range'] == "$1M-$10M"
        assert result['website'] == "https://testbrand.com"
        assert result['linkedin_url'] == "https://linkedin.com/company/testbrand"
        assert result['why_good_fit'] == "DTC wellness brand in target range"

