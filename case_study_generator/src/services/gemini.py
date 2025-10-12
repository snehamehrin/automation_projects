import logging
from typing import Dict, List
import google.generativeai as genai
from src.models.case_study import ResearchFinding
from src.utils.validation import validate_api_key

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google's Gemini API."""

    def __init__(self, api_key: str):
        """Initialize the Gemini service.
        
        Args:
            api_key: Google API key for Gemini
        """
        validate_api_key(api_key)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini service initialized")

    async def research_topic(self, topic: str, prompts: List[str]) -> List[ResearchFinding]:
        """Conduct research on a topic using Gemini.
        
        Args:
            topic: The topic to research
            prompts: List of prompts to use for research
            
        Returns:
            List of research findings
            
        Raises:
            ValueError: If topic or prompts are invalid
            RuntimeError: If API call fails
        """
        if not topic or not prompts:
            raise ValueError("Topic and prompts must not be empty")

        findings = []
        for prompt in prompts:
            try:
                formatted_prompt = prompt.format(topic=topic)
                response = await self.model.generate_content_async(formatted_prompt)
                
                finding = ResearchFinding(
                    prompt=prompt,
                    content=response.text
                )
                findings.append(finding)
                
                logger.info(f"Successfully generated research for prompt: {prompt}")
            except Exception as e:
                logger.error(f"Error generating research for prompt {prompt}: {str(e)}")
                raise RuntimeError(f"Failed to generate research: {str(e)}")

        return findings

    async def validate_response(self, response: str) -> bool:
        """Validate the response from Gemini.
        
        Args:
            response: The response to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        # Add validation logic here
        return bool(response and len(response.strip()) > 0) 