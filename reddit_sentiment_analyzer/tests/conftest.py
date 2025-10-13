"""
Test configuration and fixtures
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List


@pytest.fixture
def mock_prospect_data():
    """Sample prospect data for testing"""
    return {
        'id': 'test-prospect-123',
        'brand_name': 'Test Brand',
        'hq_location': 'San Francisco, CA',
        'industry_category': 'Wellness',
        'est_revenue_range': '$1M-$10M',
        'website': 'https://testbrand.com',
        'linkedin_url': 'https://linkedin.com/company/testbrand',
        'why_good_fit': 'DTC wellness brand in target range'
    }


@pytest.fixture
def mock_reddit_urls():
    """Sample Reddit URLs for testing"""
    return [
        'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
        'https://reddit.com/r/Wellness/comments/def456/anyone-tried-test-brand',
        'https://reddit.com/r/Health/comments/ghi789/test-brand-experience'
    ]


@pytest.fixture
def mock_reddit_data():
    """Sample Reddit post/comment data for testing"""
    return [
        {
            'id': 'post-123',
            'dataType': 'post',
            'title': 'Test Brand Review - Amazing Results!',
            'body': 'I have been using Test Brand for 3 months and the results are incredible. My energy levels have improved significantly.',
            'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
            'communityName': 'Supplements',
            'createdAt': '2024-01-15T10:30:00Z',
            'upVotes': 45,
            'commentsCount': 12,
            'category': 'review'
        },
        {
            'id': 'comment-456',
            'dataType': 'comment',
            'body': 'I agree! Test Brand has been a game changer for me too. The quality is outstanding.',
            'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
            'communityName': 'Supplements',
            'createdAt': '2024-01-15T11:15:00Z',
            'upVotes': 8,
            'numberOfReplies': 0,
            'postId': 'post-123',
            'parentId': None
        }
    ]


@pytest.fixture
def mock_google_search_results():
    """Sample Google search results for testing"""
    return [
        {
            'organicResults': [
                {
                    'url': 'https://reddit.com/r/Supplements/comments/abc123/test-brand-review',
                    'title': 'Test Brand Review - Reddit',
                    'snippet': 'Discussion about Test Brand on Reddit'
                },
                {
                    'url': 'https://reddit.com/r/Wellness/comments/def456/anyone-tried-test-brand',
                    'title': 'Anyone tried Test Brand? - Reddit',
                    'snippet': 'Reddit discussion about Test Brand experience'
                }
            ]
        }
    ]


@pytest.fixture
def mock_analysis_result():
    """Sample analysis result for testing"""
    return {
        'brand_name': 'Test Brand',
        'key_insight': 'Test Brand faces a "social proof cascade failure" - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation',
        'html_content': '<html><body><h1>Test Brand Analysis Report</h1><p>Comprehensive analysis...</p></body></html>',
        'analysis_date': '2024-01-15T12:00:00Z',
        'prospect_id': 'test-prospect-123'
    }


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = Mock()
    db.get_prospect_by_name = AsyncMock()
    db.create_prospect = AsyncMock()
    db.get_all_prospects = AsyncMock()
    db.update_prospect = AsyncMock()
    db.insert_reddit_urls = AsyncMock()
    db.get_reddit_urls = AsyncMock()
    db.insert_posts_comments = AsyncMock()
    db.insert_analysis_result = AsyncMock()
    return db


@pytest.fixture
def mock_apify_response():
    """Mock Apify API response"""
    return [
        {
            'id': 'post-123',
            'dataType': 'post',
            'title': 'Test Brand Review',
            'body': 'Great product!',
            'url': 'https://reddit.com/r/test/comments/123',
            'communityName': 'test',
            'createdAt': '2024-01-15T10:30:00Z',
            'upVotes': 10,
            'commentsCount': 5
        }
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        'choices': [
            {
                'message': {
                    'content': '''
<BRAND_NAME>
Test Brand
</BRAND_NAME>

<KEY_INSIGHT>
Test Brand faces a "social proof cascade failure" - 73% display uncertainty language typical of loss aversion psychology, particularly among wellness identity seekers requiring community validation
</KEY_INSIGHT>

<HTML_REPORT>
<html><body><h1>Test Brand Analysis</h1><p>Analysis content...</p></body></html>
</HTML_REPORT>
'''
                }
            }
        ]
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

