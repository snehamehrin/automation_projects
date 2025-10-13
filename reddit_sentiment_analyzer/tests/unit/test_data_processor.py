"""
Unit tests for data_processor module
"""

import pytest
from modules.data_processor import DataProcessor


class TestDataProcessor:
    """Test cases for DataProcessor class"""
    
    @pytest.fixture
    def data_processor(self):
        """Create DataProcessor instance"""
        return DataProcessor()
    
    @pytest.fixture
    def sample_reddit_data(self):
        """Sample Reddit data for testing"""
        return [
            {
                'post_id': 'post-1',
                'body': 'This is a great product! I love Test Brand.',
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T10:30:00Z',
                'up_votes': 10,
                'url': 'https://reddit.com/r/test/comments/1',
                'data_type': 'post'
            },
            {
                'post_id': 'post-2',
                'body': '[deleted]',  # Should be filtered
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T11:00:00Z',
                'up_votes': 0,
                'url': 'https://reddit.com/r/test/comments/2',
                'data_type': 'post'
            },
            {
                'post_id': 'post-3',
                'body': 'I am a bot and this action was performed automatically.',  # Should be filtered
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T11:30:00Z',
                'up_votes': 0,
                'url': 'https://reddit.com/r/test/comments/3',
                'data_type': 'post'
            },
            {
                'post_id': 'post-4',
                'body': 'Test Brand has been amazing for my health journey. Highly recommend!',
                'community_name': 'Wellness',
                'created_at_reddit': '2024-01-15T12:00:00Z',
                'up_votes': 15,
                'url': 'https://reddit.com/r/test/comments/4',
                'data_type': 'post'
            },
            {
                'post_id': 'post-5',
                'body': 'Short',  # Should be filtered (too short)
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T12:30:00Z',
                'up_votes': 1,
                'url': 'https://reddit.com/r/test/comments/5',
                'data_type': 'post'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_process_data_complete_pipeline(self, data_processor, sample_reddit_data):
        """Test complete data processing pipeline"""
        # Execute
        result = await data_processor.process_data(
            sample_reddit_data, "Test Brand", "test-prospect-123"
        )
        
        # Assert
        assert len(result) == 2  # Only 2 valid items should remain after filtering
        assert all(item['brandName'] == "Test Brand" for item in result)
        assert all(item['prospect_id'] == "test-prospect-123" for item in result)
        assert all(len(item['text']) <= 1200 for item in result)  # Text should be trimmed
    
    def test_filter_unwanted_content(self, data_processor, sample_reddit_data):
        """Test filtering of unwanted content"""
        # Execute
        result = data_processor._filter_unwanted(sample_reddit_data)
        
        # Assert
        assert len(result) == 2  # Only 2 items should pass filtering
        assert result[0]['post_id'] == 'post-1'
        assert result[1]['post_id'] == 'post-4'
        
        # Verify filtered items
        filtered_ids = [item['post_id'] for item in result]
        assert 'post-2' not in filtered_ids  # [deleted] content
        assert 'post-3' not in filtered_ids  # Bot content
        assert 'post-5' not in filtered_ids  # Too short content
    
    def test_filter_bot_content(self, data_processor):
        """Test filtering of bot content"""
        bot_data = [
            {'body': 'I am a bot and this action was performed automatically.'},
            {'body': 'Contact the moderators for more information.'},
            {'body': 'AutoModerator has removed this post.'},
            {'body': 'This is normal user content about Test Brand.'}
        ]
        
        result = data_processor._filter_unwanted(bot_data)
        
        assert len(result) == 1
        assert 'normal user content' in result[0]['body']
    
    def test_filter_deleted_content(self, data_processor):
        """Test filtering of deleted content"""
        deleted_data = [
            {'body': '[deleted]'},
            {'body': '[removed]'},
            {'body': 'This is valid content about Test Brand.'}
        ]
        
        result = data_processor._filter_unwanted(deleted_data)
        
        assert len(result) == 1
        assert 'valid content' in result[0]['body']
    
    def test_filter_spam_content(self, data_processor):
        """Test filtering of spam content"""
        spam_data = [
            {'body': 'Check out my website for more info!'},
            {'body': 'Follow me on Instagram for updates.'},
            {'body': 'Link in bio for more details.'},
            {'body': 'DM me for exclusive offers.'},
            {'body': 'This is legitimate discussion about Test Brand.'}
        ]
        
        result = data_processor._filter_unwanted(spam_data)
        
        assert len(result) == 1
        assert 'legitimate discussion' in result[0]['body']
    
    def test_normalize_data_structure(self, data_processor):
        """Test data normalization"""
        input_data = [
            {
                'post_id': 'post-1',
                'body': 'Test content',
                'community_name': 'Supplements',
                'created_at_reddit': '2024-01-15T10:30:00Z',
                'up_votes': 10,
                'url': 'https://reddit.com/r/test/comments/1'
            }
        ]
        
        result = data_processor._normalize(input_data, "Test Brand", "test-prospect-123")
        
        assert len(result) == 1
        assert result[0]['id'] == 'post-1'
        assert result[0]['text'] == 'Test content'
        assert result[0]['subreddit'] == 'Supplements'
        assert result[0]['createdAt'] == '2024-01-15T10:30:00Z'
        assert result[0]['upVotes'] == 10
        assert result[0]['url'] == 'https://reddit.com/r/test/comments/1'
        assert result[0]['brandName'] == 'Test Brand'
        assert result[0]['prospect_id'] == 'test-prospect-123'
    
    def test_deduplicate_data(self, data_processor):
        """Test data deduplication"""
        duplicate_data = [
            {
                'url': 'https://reddit.com/r/test/comments/1',
                'text': 'This is a duplicate post about Test Brand with the same content.'
            },
            {
                'url': 'https://reddit.com/r/test/comments/1',
                'text': 'This is a duplicate post about Test Brand with the same content.'
            },
            {
                'url': 'https://reddit.com/r/test/comments/2',
                'text': 'This is a different post about Test Brand.'
            }
        ]
        
        result = data_processor._deduplicate(duplicate_data)
        
        assert len(result) == 2  # One duplicate should be removed
        assert result[0]['text'] == 'This is a duplicate post about Test Brand with the same content.'
        assert result[1]['text'] == 'This is a different post about Test Brand.'
    
    def test_trim_text_length(self, data_processor):
        """Test text trimming to max length"""
        long_text = "This is a very long text that exceeds the maximum length limit. " * 50
        data = [
            {'text': long_text},
            {'text': 'Short text'}
        ]
        
        result = data_processor._trim_text(data, max_length=1200)
        
        assert len(result[0]['text']) == 1200
        assert result[1]['text'] == 'Short text'  # Should remain unchanged
    
    def test_empty_data_handling(self, data_processor):
        """Test handling of empty data"""
        result = data_processor._filter_unwanted([])
        assert result == []
        
        result = data_processor._normalize([], "Test Brand", "test-prospect-123")
        assert result == []
        
        result = data_processor._deduplicate([])
        assert result == []

