import logging
from typing import Optional
from notion_client import AsyncClient
from src.utils.validation import validate_api_key

logger = logging.getLogger(__name__)

class NotionService:
    """Service for interacting with Notion API."""

    def __init__(self, api_key: str, database_id: str):
        """Initialize the Notion service.
        
        Args:
            api_key: Notion API key
            database_id: ID of the Notion database
        """
        validate_api_key(api_key)
        self.client = AsyncClient(auth=api_key)
        self.database_id = database_id
        logger.info("Notion service initialized")

    async def create_page(self, title: str, content: str) -> str:
        """Create a new page in Notion.
        
        Args:
            title: Title of the page
            content: Content to add to the page
            
        Returns:
            ID of the created page
            
        Raises:
            ValueError: If title or content are invalid
            RuntimeError: If API call fails
        """
        if not title or not content:
            raise ValueError("Title and content must not be empty")

        try:
            new_page = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
            
            logger.info(f"Successfully created Notion page: {title}")
            return new_page['id']
            
        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            raise RuntimeError(f"Failed to create Notion page: {str(e)}")

    async def get_page_content(self, page_id: str) -> Optional[str]:
        """Retrieve content from a Notion page.
        
        Args:
            page_id: ID of the page to retrieve
            
        Returns:
            Content of the page, or None if not found
            
        Raises:
            ValueError: If page_id is invalid
            RuntimeError: If API call fails
        """
        if not page_id:
            raise ValueError("Page ID must not be empty")

        try:
            blocks = await self.client.blocks.children.list(block_id=page_id)
            content = ""
            
            for block in blocks['results']:
                if block['type'] == 'paragraph':
                    for text in block['paragraph']['rich_text']:
                        content += text['text']['content'] + "\n"
            
            logger.info(f"Successfully retrieved content from Notion page: {page_id}")
            return content.strip() if content else None
            
        except Exception as e:
            logger.error(f"Error retrieving Notion page content: {str(e)}")
            raise RuntimeError(f"Failed to retrieve Notion page content: {str(e)}") 