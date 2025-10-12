"""
Google Sheets service for reading brand data and writing analysis results.

This service handles all interactions with Google Sheets API including
authentication, reading brand data, and writing analysis results.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..data.models import BrandData, AnalysisResult
from ..utils.logging import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleSheetsService:
    """
    Service for interacting with Google Sheets API.
    
    Handles authentication, reading brand data, and writing analysis results
    to Google Sheets.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize the Google Sheets service."""
        self.settings = get_settings()
        self.credentials_path = credentials_path or self.settings.google_sheets_credentials_path
        self.service = None
        self._authenticated = False
    
    async def initialize(self) -> None:
        """Initialize the service and authenticate with Google."""
        if self._authenticated:
            return
        
        logger.info("Initializing Google Sheets service")
        
        try:
            # Authenticate with Google Sheets API
            await self._authenticate()
            self._authenticated = True
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise
    
    async def _authenticate(self) -> None:
        """Authenticate with Google Sheets API."""
        creds = None
        
        # Load existing credentials
        if self.credentials_path and os.path.exists(self.credentials_path):
            creds = Credentials.from_authorized_user_file(self.credentials_path, SCOPES)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Google credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            if self.credentials_path:
                with open(self.credentials_path, 'w') as token:
                    token.write(creds.to_json())
        
        # Build the service
        self.service = build('sheets', 'v4', credentials=creds)
    
    async def load_brands(self, sheet_id: str, sheet_name: str = "Sheet1") -> List[BrandData]:
        """
        Load brand data from a Google Sheet.
        
        Args:
            sheet_id: Google Sheet ID
            sheet_name: Name of the sheet tab
            
        Returns:
            List of BrandData objects
        """
        if not self._authenticated:
            await self.initialize()
        
        logger.info(f"Loading brands from sheet: {sheet_id}")
        
        try:
            # Read data from the sheet
            range_name = f"{sheet_name}!A:Z"  # Read all columns
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning(f"No data found in sheet {sheet_id}")
                return []
            
            # Parse header row
            headers = [col.lower().strip() for col in values[0]]
            logger.debug(f"Sheet headers: {headers}")
            
            # Find required columns
            brand_col = self._find_column_index(headers, ['brand', 'company name', 'name'])
            category_col = self._find_column_index(headers, ['category', 'industry', 'sector'])
            url_col = self._find_column_index(headers, ['url', 'website', 'company url', 'linkedin company profile'])
            
            if brand_col is None:
                raise ValueError("Brand name column not found in sheet")
            
            # Parse brand data
            brands = []
            for i, row in enumerate(values[1:], start=2):  # Skip header row
                try:
                    # Ensure row has enough columns
                    while len(row) <= max(filter(None, [brand_col, category_col, url_col])):
                        row.append('')
                    
                    brand_name = row[brand_col].strip() if brand_col < len(row) else ''
                    category = row[category_col].strip() if category_col and category_col < len(row) else ''
                    company_url = row[url_col].strip() if url_col and url_col < len(row) else ''
                    
                    if brand_name:  # Only add non-empty brand names
                        brands.append(BrandData(
                            name=brand_name,
                            category=category or None,
                            company_url=company_url or None
                        ))
                
                except Exception as e:
                    logger.warning(f"Failed to parse row {i}: {e}")
                    continue
            
            logger.info(f"Loaded {len(brands)} brands from sheet")
            return brands
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading brands from sheet: {e}")
            raise
    
    async def save_analysis_results(
        self, 
        sheet_id: str, 
        results: List[AnalysisResult],
        sheet_name: str = "Sheet1"
    ) -> None:
        """
        Save analysis results to a Google Sheet.
        
        Args:
            sheet_id: Google Sheet ID
            results: List of analysis results to save
            sheet_name: Name of the sheet tab
        """
        if not self._authenticated:
            await self.initialize()
        
        if not results:
            logger.warning("No results to save")
            return
        
        logger.info(f"Saving {len(results)} analysis results to sheet: {sheet_id}")
        
        try:
            # Prepare data for writing
            values = []
            
            # Add header row
            headers = [
                'Brand Name',
                'Category',
                'Company URL',
                'Analysis Timestamp',
                'Total Posts',
                'Key Insight',
                'Sentiment Summary',
                'Thematic Breakdown',
                'Customer Segments',
                'Strategic Recommendations',
                'HTML Report'
            ]
            values.append(headers)
            
            # Add data rows
            for result in results:
                row = [
                    result.brand_name,
                    result.brand_category or '',
                    result.company_url or '',
                    result.analysis_timestamp.isoformat(),
                    str(result.total_posts),
                    result.key_insight,
                    str(result.sentiment_summary),
                    '; '.join(result.thematic_breakdown),
                    '; '.join(result.customer_segments),
                    '; '.join(result.strategic_recommendations),
                    result.html_report[:1000] + '...' if len(result.html_report) > 1000 else result.html_report
                ]
                values.append(row)
            
            # Write to sheet
            range_name = f"{sheet_name}!A:K"
            body = {'values': values}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully saved {len(results)} results to sheet")
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving results to sheet: {e}")
            raise
    
    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """Find the index of a column by matching possible names."""
        for name in possible_names:
            for i, header in enumerate(headers):
                if name in header:
                    return i
        return None
    
    async def test_connection(self, sheet_id: str) -> bool:
        """
        Test connection to a Google Sheet.
        
        Args:
            sheet_id: Google Sheet ID to test
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._authenticated:
                await self.initialize()
            
            # Try to read a small range
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range="Sheet1!A1:A1"
            ).execute()
            
            logger.info(f"Successfully connected to sheet: {sheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to sheet {sheet_id}: {e}")
            return False
    
    async def close(self) -> None:
        """Close the service and clean up resources."""
        logger.info("Closing Google Sheets service")
        self.service = None
        self._authenticated = False
