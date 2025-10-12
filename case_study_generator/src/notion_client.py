import os
from notion_client import Client
from dotenv import load_dotenv

class NotionClient:
    def __init__(self):
        load_dotenv()
        self.client = Client(auth=os.getenv('NOTION_API_KEY'))
        self.database_id = os.getenv('NOTION_DATABASE_ID')

    def create_page(self, title: str, content: str) -> str:
        """
        Create a new page in Notion with the research content.
        
        Args:
            title (str): Title of the page
            content (str): Content to add to the page
            
        Returns:
            str: ID of the created page
        """
        new_page = self.client.pages.create(
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
        
        return new_page['id']

    def get_page_content(self, page_id: str) -> str:
        """
        Retrieve content from a Notion page.
        
        Args:
            page_id (str): ID of the page to retrieve
            
        Returns:
            str: Content of the page
        """
        blocks = self.client.blocks.children.list(block_id=page_id)
        content = ""
        
        for block in blocks['results']:
            if block['type'] == 'paragraph':
                for text in block['paragraph']['rich_text']:
                    content += text['text']['content'] + "\n"
                    
        return content 