"""
Pytest configuration and fixtures for the Reddit Sentiment Analyzer.

This module provides shared fixtures and configuration for all tests.
"""

import asyncio
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData, RedditPost, DataType
from src.services.google_sheets import GoogleSheetsService
from src.services.apify import ApifyService
from src.services.openai import OpenAIService
from src.data.processors import DataProcessor


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_google_sheets_service() -> AsyncMock:
    """Mock Google Sheets service."""
    service = AsyncMock(spec=GoogleSheetsService)
    service.initialize = AsyncMock()
    service.load_brands = AsyncMock(return_value=[
        BrandData(name="Test Brand", category="Test Category")
    ])
    service.save_analysis_results = AsyncMock()
    service.test_connection = AsyncMock(return_value=True)
    service.close = AsyncMock()
    return service


@pytest.fixture
async def mock_apify_service() -> AsyncMock:
    """Mock Apify service."""
    service = AsyncMock(spec=ApifyService)
    service.initialize = AsyncMock()
    service.google_search = AsyncMock(return_value={
        "organicResults": [
            {"url": "https://reddit.com/r/test/comments/abc123", "title": "Test Post"}
        ]
    })
    service.scrape_reddit = AsyncMock(return_value=[
        {
            "id": "abc123",
            "text": "This is a test post about the brand.",
            "dataType": "post",
            "title": "Test Post",
            "communityName": "test",
            "upVotes": 10,
            "createdAt": "2024-01-15T10:30:00Z"
        }
    ])
    service.test_connection = AsyncMock(return_value=True)
    service.close = AsyncMock()
    return service


@pytest.fixture
async def mock_openai_service() -> AsyncMock:
    """Mock OpenAI service."""
    service = AsyncMock(spec=OpenAIService)
    service.initialize = AsyncMock()
    service.analyze_sentiment = AsyncMock(return_value={
        "brand_name": "Test Brand",
        "key_insight": "Test brand faces a 'test phenomenon' - 50% of discussions are positive.",
        "html_report": "<html><body>Test report</body></html>",
        "sentiment_summary": {"positive": 50, "negative": 30, "neutral": 20, "total": 100},
        "thematic_breakdown": ["Quality", "Price", "Service"],
        "customer_segments": ["Segment 1", "Segment 2"],
        "strategic_recommendations": ["Recommendation 1", "Recommendation 2"]
    })
    service.test_connection = AsyncMock(return_value=True)
    service.close = AsyncMock()
    return service


@pytest.fixture
async def mock_data_processor() -> AsyncMock:
    """Mock data processor."""
    processor = AsyncMock(spec=DataProcessor)
    processor.initialize = AsyncMock()
    processor.process_posts = AsyncMock(return_value=[
        RedditPost(
            id="abc123",
            text="This is a test post about the brand.",
            data_type=DataType.POST,
            title="Test Post",
            community="test",
            up_votes=10
        )
    ])
    processor.close = AsyncMock()
    return processor


@pytest.fixture
async def analyzer_with_mocks(
    mock_google_sheets_service,
    mock_apify_service,
    mock_openai_service,
    mock_data_processor
) -> RedditSentimentAnalyzer:
    """Create analyzer with mocked services."""
    analyzer = RedditSentimentAnalyzer(
        google_sheets_service=mock_google_sheets_service,
        apify_service=mock_apify_service,
        openai_service=mock_openai_service,
        data_processor=mock_data_processor
    )
    
    await analyzer.initialize()
    yield analyzer
    await analyzer.close()


@pytest.fixture
def sample_brand_data() -> BrandData:
    """Sample brand data for testing."""
    return BrandData(
        name="Test Brand",
        category="Test Category",
        company_url="https://testbrand.com"
    )


@pytest.fixture
def sample_reddit_posts() -> list[RedditPost]:
    """Sample Reddit posts for testing."""
    return [
        RedditPost(
            id="post1",
            text="I love this brand! Great quality and service.",
            data_type=DataType.POST,
            title="Amazing experience with Test Brand",
            community="reviews",
            up_votes=15,
            author="user1",
            brand_name="Test Brand"
        ),
        RedditPost(
            id="post2",
            text="Not impressed with the quality. Expected better.",
            data_type=DataType.POST,
            title="Disappointed with Test Brand",
            community="reviews",
            up_votes=5,
            author="user2",
            brand_name="Test Brand"
        ),
        RedditPost(
            id="comment1",
            text="I agree, the service was excellent.",
            data_type=DataType.COMMENT,
            post_id="post1",
            author="user3",
            brand_name="Test Brand"
        )
    ]


@pytest.fixture
def temp_file() -> Generator:
    """Temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        yield f.name


@pytest.fixture
def sample_analysis_data() -> dict:
    """Sample analysis data for testing."""
    return {
        "brand": "Test Brand",
        "category": "Test Category",
        "company_url": "https://testbrand.com",
        "posts": [
            {
                "id": "post1",
                "text": "I love this brand! Great quality and service.",
                "subreddit": "reviews",
                "upVotes": 15,
                "createdAt": "2024-01-15T10:30:00Z",
                "brandName": "Test Brand"
            }
        ]
    }


@pytest.fixture
def sample_openai_response() -> str:
    """Sample OpenAI response for testing."""
    return """
    <BRAND_NAME>
    Test Brand
    </BRAND_NAME>
    <KEY_INSIGHT>
    Test Brand faces a 'quality perception gap' - 40% of discussions mention durability concerns, particularly among long-term users seeking value for money.
    </KEY_INSIGHT>
    <HTML_REPORT>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Brand Intelligence Report - Test Brand</title>
    </head>
    <body>
        <h1>BRAND INTELLIGENCE REPORT</h1>
        <h2>TEST BRAND - Reddit Consumer Intelligence Analysis</h2>
        <div class="key-insight">
            KEY INSIGHT: Test Brand faces a 'quality perception gap' - 40% of discussions mention durability concerns, particularly among long-term users seeking value for money.
        </div>
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-number">100</div>
                <div class="stat-label">TOTAL POSTS</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">50%</div>
                <div class="stat-label">POSITIVE</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">30%</div>
                <div class="stat-label">NEGATIVE</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">20%</div>
                <div class="stat-label">NEUTRAL</div>
            </div>
        </div>
    </body>
    </html>
    </HTML_REPORT>
    """


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing."""
    client = AsyncMock()
    client.post = AsyncMock()
    client.get = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client


# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("APIFY_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")


# Async test markers
pytest_plugins = ["pytest_asyncio"]
