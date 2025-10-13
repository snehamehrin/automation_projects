"""
Module 4: Data Processor
Cleans, deduplicates, and filters Reddit data
"""

from typing import List, Dict, Any, Set
from utils.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    def __init__(self):
        self.filter_patterns = {
            'bot': [
                "I am a bot",
                "action was performed automatically",
                "contact the moderators",
                "AutoModerator"
            ],
            'deleted': ["[deleted]", "[removed]"],
            'moderator': [
                "Discussion in this subreddit",
                "Please vote accordingly",
                "peer reviewed sources"
            ],
            'welcome': ["Welcome to", "welcome to the", "Thanks for joining"],
            'spam': ["check out my", "follow me on", "link in bio", "dm me for"]
        }
    
    async def process_data(
        self, 
        data: List[Dict[str, Any]], 
        brand_name: str, 
        prospect_id: str
    ) -> List[Dict[str, Any]]:
        """Process raw Reddit data through cleaning pipeline"""
        logger.info(f"Processing {len(data)} items")
        
        # Step 1: Filter bot/spam/deleted content
        filtered = self._filter_unwanted(data)
        logger.info(f"After filtering: {len(filtered)} items")
        
        # Step 2: Normalize
        normalized = self._normalize(filtered, brand_name, prospect_id)
        
        # Step 3: Deduplicate
        deduped = self._deduplicate(normalized)
        logger.info(f"After deduplication: {len(deduped)} items")
        
        # Step 4: Trim text length
        trimmed = self._trim_text(deduped, max_length=1200)
        
        return trimmed
    
    def _filter_unwanted(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out bot posts, spam, deleted content"""
        filtered = []
        
        for item in data:
            text = (item.get('body') or '').lower()
            
            # Skip empty
            if not text or len(text) < 20:
                continue
            
            # Check filter patterns
            should_filter = False
            for category, patterns in self.filter_patterns.items():
                if any(pattern.lower() in text for pattern in patterns):
                    should_filter = True
                    break
            
            if not should_filter:
                filtered.append(item)
        
        return filtered
    
    def _normalize(
        self, 
        data: List[Dict[str, Any]], 
        brand_name: str, 
        prospect_id: str
    ) -> List[Dict[str, Any]]:
        """Normalize data structure"""
        normalized = []
        
        for item in data:
            normalized.append({
                'id': item.get('post_id'),
                'text': item.get('body', '').strip(),
                'subreddit': item.get('community_name'),
                'createdAt': item.get('created_at_reddit'),
                'upVotes': item.get('up_votes', 0),
                'url': item.get('url'),
                'brandName': brand_name,
                'prospect_id': prospect_id
            })
        
        return normalized
    
    def _deduplicate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on URL + text snippet"""
        seen: Set[str] = set()
        deduped = []
        
        for item in data:
            key = f"{item.get('url', '')}|{item['text'][:160]}"
            
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        
        return deduped
    
    def _trim_text(self, data: List[Dict[str, Any]], max_length: int) -> List[Dict[str, Any]]:
        """Trim text to max length"""
        for item in data:
            if len(item['text']) > max_length:
                item['text'] = item['text'][:max_length]
        
        return data

