import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiResearch:
    def __init__(self):
        load_dotenv()
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')

    def research_topic(self, topic: str, prompts: list) -> dict:
        """
        Conduct research on a topic using Gemini AI.
        
        Args:
            topic (str): The topic to research
            prompts (list): List of prompts to use for research
            
        Returns:
            dict: Research results organized by prompt
        """
        results = {}
        
        for prompt in prompts:
            formatted_prompt = prompt.format(topic=topic)
            response = self.model.generate_content(formatted_prompt)
            results[prompt] = response.text
            
        return results

    def format_research(self, research_results: dict) -> str:
        """
        Format research results for Notion storage.
        
        Args:
            research_results (dict): Raw research results
            
        Returns:
            str: Formatted research text
        """
        formatted_text = "# Research Results\n\n"
        
        for prompt, result in research_results.items():
            formatted_text += f"## {prompt}\n\n{result}\n\n"
            
        return formatted_text 