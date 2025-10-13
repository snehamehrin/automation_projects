#!/usr/bin/env python3
"""
Process the existing scraped data and save it to database
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_existing_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Process existing scraped data and save to database."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ DataProcessor initialized successfully")
    
    def process_reddit_data(self, reddit_data: List[Dict[str, Any]], brand_name: str) -> List[Dict[str, Any]]:
        """Process Reddit data into the correct format for database."""
        logger.info(f"🔄 Processing {len(reddit_data)} Reddit items for brand: {brand_name}")
        processed_data = []
        
        posts_count = 0
        comments_count = 0
        
        for item in reddit_data:
            data_type = item.get('dataType')
            
            if data_type == 'post':
                # Extract post body text (title + body)
                title = item.get('title', '')
                body = item.get('body', '')
                full_text = f"{title}. {body}".strip()
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('id', ''),
                    'parent_id': None,
                    'category': 'post',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'post',
                    'brand_name': brand_name,
                    'body': full_text
                }
                processed_data.append(processed_item)
                posts_count += 1
                logger.debug(f"Processed post: {title[:50]}...")
                
            elif data_type == 'comment':
                # Extract comment body text
                comment_body = item.get('body', '')
                
                processed_item = {
                    'url': item.get('url', ''),
                    'post_id': item.get('postId', ''),
                    'parent_id': item.get('parentId', ''),
                    'category': 'comment',
                    'community_name': item.get('communityName', ''),
                    'created_at_reddit': item.get('createdAt', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'up_votes': item.get('upVotes', 0),
                    'number_of_replies': item.get('numberOfReplies', 0),
                    'data_type': 'comment',
                    'brand_name': brand_name,
                    'body': comment_body
                }
                processed_data.append(processed_item)
                comments_count += 1
                logger.debug(f"Processed comment: {comment_body[:50]}...")
            else:
                logger.warning(f"Unknown dataType: {data_type} for item: {item.get('id', 'unknown')}")
        
        logger.info(f"✅ Processed {posts_count} posts and {comments_count} comments")
        return processed_data
    
    async def save_reddit_data(self, reddit_data: List[Dict[str, Any]]) -> bool:
        """Save Reddit data to database."""
        logger.info(f"💾 Saving {len(reddit_data)} Reddit items to database...")
        
        try:
            # Log sample data structure
            if reddit_data:
                sample_item = reddit_data[0]
                logger.debug(f"Sample item structure: {list(sample_item.keys())}")
                logger.debug(f"Sample item: {json.dumps(sample_item, indent=2, default=str)}")
            
            response = self.supabase.table('brand_reddit_posts_comments').insert(reddit_data).execute()
            
            if response.data:
                logger.info(f"✅ Successfully saved {len(response.data)} Reddit items to database")
                
                # Show summary
                posts_count = len([item for item in reddit_data if item['data_type'] == 'post'])
                comments_count = len([item for item in reddit_data if item['data_type'] == 'comment'])
                
                logger.info(f"📋 Summary:")
                logger.info(f"   Posts saved: {posts_count}")
                logger.info(f"   Comments saved: {comments_count}")
                logger.info(f"   Total items: {len(response.data)}")
                logger.info(f"   Table: brand_reddit_posts_comments")
                
                return True
            else:
                logger.error("❌ No data returned from database insert")
                logger.error(f"Response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    async def process_from_log_file(self, log_file_path: str):
        """Process data from a log file that contains scraped data."""
        logger.info(f"📖 Reading data from log file: {log_file_path}")
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the JSON data in the log file
            # Look for the start of the JSON array
            start_idx = content.find('[')
            if start_idx == -1:
                logger.error("❌ No JSON array found in log file")
                return
            
            # Find the end of the JSON array
            end_idx = content.rfind(']') + 1
            if end_idx == 0:
                logger.error("❌ No end of JSON array found in log file")
                return
            
            # Extract the JSON data
            json_str = content[start_idx:end_idx]
            
            try:
                reddit_data = json.loads(json_str)
                logger.info(f"✅ Successfully parsed {len(reddit_data)} items from log file")
                
                # Process the data
                processed_data = self.process_reddit_data(reddit_data, "Knix")  # Assuming Knix brand
                
                if processed_data:
                    # Save to database
                    success = await self.save_reddit_data(processed_data)
                    
                    if success:
                        logger.info("🎉 Successfully processed and saved data from log file!")
                    else:
                        logger.error("❌ Failed to save data to database")
                else:
                    logger.error("❌ No data was processed")
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parsing JSON: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error reading log file: {e}")


async def main():
    """Main function."""
    logger.info("🚀 Process Existing Scraped Data")
    logger.info("=" * 50)
    
    try:
        processor = DataProcessor()
        
        # Process the most recent log file
        log_file = "save_scraped_data.log"
        
        if os.path.exists(log_file):
            logger.info(f"📁 Found log file: {log_file}")
            await processor.process_from_log_file(log_file)
        else:
            logger.error(f"❌ Log file not found: {log_file}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
