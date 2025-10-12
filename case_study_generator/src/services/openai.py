import logging
from typing import Dict, List
from openai import AsyncOpenAI
from src.models.case_study import SynthesisResult
from src.utils.validation import validate_api_key

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self, api_key: str):
        """Initialize the OpenAI service.
        
        Args:
            api_key: OpenAI API key
        """
        validate_api_key(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI service initialized")

    async def synthesize_themes(self, content: str, prompts: List[str]) -> SynthesisResult:
        """Synthesize themes from content using OpenAI.
        
        Args:
            content: The content to analyze
            prompts: List of prompts for synthesis
            
        Returns:
            SynthesisResult containing themes, insights, and recommendations
            
        Raises:
            ValueError: If content or prompts are invalid
            RuntimeError: If API call fails
        """
        if not content or not prompts:
            raise ValueError("Content and prompts must not be empty")

        try:
            synthesis = SynthesisResult()
            
            for prompt in prompts:
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a research analyst synthesizing key themes and insights."
                        },
                        {
                            "role": "user",
                            "content": f"{prompt}\n\nContent to analyze:\n{content}"
                        }
                    ]
                )
                
                result = response.choices[0].message.content
                
                # Categorize the result based on the prompt
                if "themes" in prompt.lower():
                    synthesis.key_themes.append(result)
                elif "insights" in prompt.lower():
                    synthesis.insights.append(result)
                elif "recommendations" in prompt.lower():
                    synthesis.recommendations.append(result)
                
                logger.info(f"Successfully generated synthesis for prompt: {prompt}")
                
            return synthesis
            
        except Exception as e:
            logger.error(f"Error generating synthesis: {str(e)}")
            raise RuntimeError(f"Failed to generate synthesis: {str(e)}")

    async def validate_response(self, response: str) -> bool:
        """Validate the response from OpenAI.
        
        Args:
            response: The response to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        return bool(response and len(response.strip()) > 0) 