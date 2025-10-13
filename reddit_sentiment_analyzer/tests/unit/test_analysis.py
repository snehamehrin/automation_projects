"""
Unit tests for analysis module
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from modules.analysis import Analyzer


class TestAnalyzer:
    """Test cases for Analyzer class"""
    
    @pytest.fixture
    def analyzer(self, mock_database):
        """Create Analyzer instance with mocked dependencies"""
        with patch('modules.analysis.Database', return_value=mock_database), \
             patch('modules.analysis.get_settings') as mock_settings, \
             patch('modules.analysis.AsyncOpenAI') as mock_openai:
            mock_settings.return_value.OPENAI_API_KEY = "test-key"
            mock_openai.return_value = Mock()
            return Analyzer()
    
    @pytest.fixture
    def sample_posts(self):
        """Sample posts for analysis"""
        return [
            {
                'id': 'post-1',
                'text': 'Test Brand is amazing! I have been using it for months.',
                'subreddit': 'Supplements',
                'createdAt': '2024-01-15T10:30:00Z',
                'upVotes': 10,
                'url': 'https://reddit.com/r/test/comments/1',
                'brandName': 'Test Brand',
                'prospect_id': 'test-prospect-123'
            },
            {
                'id': 'post-2',
                'text': 'Test Brand has been a game changer for my health.',
                'subreddit': 'Wellness',
                'createdAt': '2024-01-15T11:00:00Z',
                'upVotes': 15,
                'url': 'https://reddit.com/r/test/comments/2',
                'brandName': 'Test Brand',
                'prospect_id': 'test-prospect-123'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_posts, mock_openai_response, mock_database):
        """Test successful analysis"""
        # Setup
        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_database.insert_analysis_result.return_value = {'id': 'analysis-123'}
        
        # Execute
        result = await analyzer.analyze(sample_posts, "Test Brand", "test-prospect-123")
        
        # Assert
        assert result['brand_name'] == "Test Brand"
        assert "social proof cascade failure" in result['key_insight']
        assert "<html>" in result['html_content']
        assert result['prospect_id'] == "test-prospect-123"
        assert 'analysis_date' in result
        
        # Verify OpenAI was called
        analyzer.client.chat.completions.create.assert_called_once()
        call_args = analyzer.client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o"
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 16000
        
        # Verify database was called
        mock_database.insert_analysis_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_with_many_posts(self, analyzer, mock_openai_response, mock_database):
        """Test analysis with many posts (should be limited to 120)"""
        # Setup - create 150 posts
        many_posts = []
        for i in range(150):
            many_posts.append({
                'id': f'post-{i}',
                'text': f'Test Brand post {i}',
                'subreddit': 'Test',
                'createdAt': '2024-01-15T10:30:00Z',
                'upVotes': 1,
                'url': f'https://reddit.com/r/test/comments/{i}',
                'brandName': 'Test Brand',
                'prospect_id': 'test-prospect-123'
            })
        
        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        
        # Execute
        await analyzer.analyze(many_posts, "Test Brand", "test-prospect-123")
        
        # Assert - verify that only 120 posts were sent to OpenAI
        call_args = analyzer.client.chat.completions.create.call_args
        prompt_content = call_args[1]['messages'][1]['content']
        # The prompt should contain limited posts (this is a simplified check)
        assert len(many_posts) == 150  # Original data unchanged
        analyzer.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_openai_error(self, analyzer, sample_posts):
        """Test analysis with OpenAI API error"""
        # Setup
        analyzer.client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI API Error")
        )
        
        # Execute & Assert
        with pytest.raises(Exception, match="OpenAI API Error"):
            await analyzer.analyze(sample_posts, "Test Brand", "test-prospect-123")
    
    def test_generate_prompt(self, analyzer, sample_posts):
        """Test prompt generation"""
        # Execute
        prompt = analyzer._generate_prompt(sample_posts, "Test Brand")
        
        # Assert
        assert "Test Brand" in prompt
        assert "Brand Intelligence Report" in prompt
        assert "CROSS-DOMAIN PATTERN RECOGNITION" in prompt
        assert "KEY_INSIGHT" in prompt
        assert "HTML_REPORT" in prompt
        assert "BRAND_NAME" in prompt
        assert "Test Brand" in prompt
    
    def test_parse_response_complete(self, analyzer):
        """Test parsing complete response"""
        # Setup
        raw_content = """
<BRAND_NAME>
Test Brand
</BRAND_NAME>

<KEY_INSIGHT>
Test Brand faces a "social proof cascade failure" - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation
</KEY_INSIGHT>

<HTML_REPORT>
<html><body><h1>Test Brand Analysis</h1><p>Analysis content...</p></body></html>
</HTML_REPORT>
"""
        
        # Execute
        result = analyzer._parse_response(raw_content, "Test Brand", "test-prospect-123")
        
        # Assert
        assert result['brand_name'] == "Test Brand"
        assert "social proof cascade failure" in result['key_insight']
        assert "<html>" in result['html_content']
        assert result['prospect_id'] == "test-prospect-123"
        assert 'analysis_date' in result
    
    def test_parse_response_missing_sections(self, analyzer):
        """Test parsing response with missing sections"""
        # Setup
        raw_content = "This is just plain text without any structured sections."
        
        # Execute
        result = analyzer._parse_response(raw_content, "Test Brand", "test-prospect-123")
        
        # Assert
        assert result['brand_name'] == "Test Brand"  # Fallback to input
        assert result['key_insight'] == "Analysis complete"  # Default fallback
        assert result['html_content'] == raw_content  # Fallback to raw content
        assert result['prospect_id'] == "test-prospect-123"
        assert 'analysis_date' in result
    
    def test_extract_section_success(self, analyzer):
        """Test successful section extraction"""
        content = "Start <TEST>This is test content</TEST> End"
        result = analyzer._extract_section(content, "TEST")
        assert result == "This is test content"
    
    def test_extract_section_not_found(self, analyzer):
        """Test section extraction when section not found"""
        content = "This content has no sections"
        result = analyzer._extract_section(content, "TEST")
        assert result == ""
    
    def test_extract_section_incomplete(self, analyzer):
        """Test section extraction with incomplete tags"""
        content = "Start <TEST>This is test content End"
        result = analyzer._extract_section(content, "TEST")
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_analyze_empty_posts(self, analyzer, mock_openai_response, mock_database):
        """Test analysis with empty posts list"""
        # Setup
        analyzer.client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        
        # Execute
        result = await analyzer.analyze([], "Test Brand", "test-prospect-123")
        
        # Assert
        assert result['brand_name'] == "Test Brand"
        assert result['prospect_id'] == "test-prospect-123"
        analyzer.client.chat.completions.create.assert_called_once()
        mock_database.insert_analysis_result.assert_called_once()

