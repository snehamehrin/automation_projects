import logging
from typing import List, Optional
from src.services.gemini import GeminiService
from src.services.notion import NotionService
from src.models.case_study import ResearchFinding
from src.utils.validation import validate_topic
from src.utils.formatting import format_research_for_notion

logger = logging.getLogger(__name__)

class ResearchOrchestrator:
    """Orchestrates the research process using Gemini and Notion."""

    def __init__(
        self,
        gemini_service: GeminiService,
        notion_service: NotionService,
        prompts: List[str]
    ):
        """Initialize the research orchestrator.
        
        Args:
            gemini_service: Initialized Gemini service
            notion_service: Initialized Notion service
            prompts: List of research prompts
        """
        self.gemini = gemini_service
        self.notion = notion_service
        self.prompts = prompts
        logger.info("Research orchestrator initialized")

    async def conduct_research(self, topic: str) -> tuple[List[ResearchFinding], str]:
        """Conduct research on a topic.
        
        Args:
            topic: The topic to research
            
        Returns:
            Tuple of (research findings, Notion page ID)
            
        Raises:
            ValueError: If topic is invalid
            RuntimeError: If research process fails
        """
        try:
            # Validate topic
            validate_topic(topic)
            
            # Conduct research
            logger.info(f"Starting research on topic: {topic}")
            findings = await self.gemini.research_topic(topic, self.prompts)
            
            # Format for Notion
            formatted_research = format_research_for_notion({
                f.prompt: f.content for f in findings
            })
            
            # Store in Notion
            notion_page_id = await self.notion.create_page(
                f"Research: {topic}",
                formatted_research
            )
            
            logger.info(f"Research completed and stored in Notion (Page ID: {notion_page_id})")
            return findings, notion_page_id
            
        except Exception as e:
            logger.error(f"Research process failed: {str(e)}")
            raise RuntimeError(f"Research process failed: {str(e)}")

    async def validate_findings(self, findings: List[ResearchFinding]) -> bool:
        """Validate research findings.
        
        Args:
            findings: List of research findings
            
        Returns:
            True if all findings are valid, False otherwise
        """
        if not findings:
            return False
            
        for finding in findings:
            if not await self.gemini.validate_response(finding.content):
                return False
                
        return True 