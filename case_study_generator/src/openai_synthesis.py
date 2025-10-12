import os
from openai import OpenAI
from dotenv import load_dotenv

class OpenAISynthesis:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def synthesize_themes(self, content: str, prompts: list) -> dict:
        """
        Synthesize key themes from research content using OpenAI.
        
        Args:
            content (str): Research content to analyze
            prompts (list): List of prompts for synthesis
            
        Returns:
            dict: Synthesized themes and insights
        """
        results = {}
        
        for prompt in prompts:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a research analyst synthesizing key themes and insights."},
                    {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{content}"}
                ]
            )
            results[prompt] = response.choices[0].message.content
            
        return results

    def format_synthesis(self, synthesis_results: dict) -> dict:
        """
        Format synthesis results into structured data.
        
        Args:
            synthesis_results (dict): Raw synthesis results
            
        Returns:
            dict: Structured synthesis data
        """
        structured_data = {
            "key_themes": [],
            "insights": [],
            "recommendations": []
        }
        
        for prompt, result in synthesis_results.items():
            if "themes" in prompt.lower():
                structured_data["key_themes"].append(result)
            elif "insights" in prompt.lower():
                structured_data["insights"].append(result)
            elif "recommendations" in prompt.lower():
                structured_data["recommendations"].append(result)
                
        return structured_data 