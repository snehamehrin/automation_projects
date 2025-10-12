import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.research import ResearchOrchestrator
from src.models.case_study import ResearchFinding

@pytest.fixture
def mock_gemini_service():
    service = AsyncMock()
    service.research_topic.return_value = [
        ResearchFinding(
            prompt="Test prompt",
            content="Test content"
        )
    ]
    service.validate_response.return_value = True
    return service

@pytest.fixture
def mock_notion_service():
    service = AsyncMock()
    service.create_page.return_value = "test-page-id"
    return service

@pytest.fixture
def research_orchestrator(mock_gemini_service, mock_notion_service):
    return ResearchOrchestrator(
        gemini_service=mock_gemini_service,
        notion_service=mock_notion_service,
        prompts=["Test prompt"]
    )

@pytest.mark.asyncio
async def test_conduct_research(research_orchestrator, mock_gemini_service, mock_notion_service):
    # Arrange
    topic = "Test Topic"
    
    # Act
    findings, notion_page_id = await research_orchestrator.conduct_research(topic)
    
    # Assert
    assert len(findings) == 1
    assert findings[0].prompt == "Test prompt"
    assert findings[0].content == "Test content"
    assert notion_page_id == "test-page-id"
    
    # Verify service calls
    mock_gemini_service.research_topic.assert_called_once_with(topic, ["Test prompt"])
    mock_notion_service.create_page.assert_called_once()

@pytest.mark.asyncio
async def test_validate_findings(research_orchestrator, mock_gemini_service):
    # Arrange
    findings = [
        ResearchFinding(
            prompt="Test prompt",
            content="Test content"
        )
    ]
    
    # Act
    result = await research_orchestrator.validate_findings(findings)
    
    # Assert
    assert result is True
    mock_gemini_service.validate_response.assert_called_once_with("Test content")

@pytest.mark.asyncio
async def test_conduct_research_invalid_topic(research_orchestrator):
    # Arrange
    topic = ""
    
    # Act & Assert
    with pytest.raises(ValueError):
        await research_orchestrator.conduct_research(topic) 