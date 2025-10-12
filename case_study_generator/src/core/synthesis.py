import logging
from typing import List, Optional
from src.services.openai import OpenAIService
from src.models.case_study import SynthesisResult
from src.utils.formatting import format_synthesis_for_yaml

logger = logging.getLogger(__name__)

class SynthesisOrchestrator:
    """Orchestrates the synthesis process using OpenAI."""

    def __init__(
        self,
        openai_service: OpenAIService,
        prompts: List[str]
    ):
        """Initialize the synthesis orchestrator.
        
        Args:
            openai_service: Initialized OpenAI service
            prompts: List of synthesis prompts
        """
        self.openai = openai_service
        self.prompts = prompts
        logger.info("Synthesis orchestrator initialized")

    async def synthesize_content(self, content: str) -> SynthesisResult:
        """Synthesize content using OpenAI.
        
        Args:
            content: The content to synthesize
            
        Returns:
            SynthesisResult containing themes, insights, and recommendations
            
        Raises:
            ValueError: If content is invalid
            RuntimeError: If synthesis process fails
        """
        try:
            if not content:
                raise ValueError("Content must not be empty")
            
            logger.info("Starting content synthesis")
            synthesis = await self.openai.synthesize_themes(content, self.prompts)
            
            # Format for YAML
            formatted_synthesis = format_synthesis_for_yaml(synthesis.dict())
            
            logger.info("Synthesis completed successfully")
            return SynthesisResult(**formatted_synthesis)
            
        except Exception as e:
            logger.error(f"Synthesis process failed: {str(e)}")
            raise RuntimeError(f"Synthesis process failed: {str(e)}")

    async def validate_synthesis(self, synthesis: SynthesisResult) -> bool:
        """Validate synthesis results.
        
        Args:
            synthesis: Synthesis results to validate
            
        Returns:
            True if synthesis is valid, False otherwise
        """
        if not synthesis:
            return False
            
        # Check if we have at least one theme or insight
        if not synthesis.key_themes and not synthesis.insights:
            return False
            
        # Validate each component
        for theme in synthesis.key_themes:
            if not await self.openai.validate_response(theme):
                return False
                
        for insight in synthesis.insights:
            if not await self.openai.validate_response(insight):
                return False
                
        return True 