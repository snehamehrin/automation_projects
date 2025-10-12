import os
import yaml
from src.gemini_research import GeminiResearch
from src.notion_client import NotionClient
from src.openai_synthesis import OpenAISynthesis
from src.yaml_generator import YAMLGenerator

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    # Load configuration
    config = load_config()
    
    # Initialize components
    gemini = GeminiResearch()
    notion = NotionClient()
    openai = OpenAISynthesis()
    yaml_gen = YAMLGenerator(config)
    
    # Get topic from user
    topic = input("Enter the topic for the case study: ")
    
    # Conduct research using Gemini
    print("Conducting research...")
    research_results = gemini.research_topic(topic, config['research_prompts']['gemini'])
    
    # Format and store research in Notion
    print("Storing research in Notion...")
    formatted_research = gemini.format_research(research_results)
    notion_page_id = notion.create_page(f"Research: {topic}", formatted_research)
    
    # Synthesize themes using OpenAI
    print("Synthesizing themes...")
    synthesis_results = openai.synthesize_themes(
        formatted_research,
        config['synthesis_prompts']['openai']
    )
    structured_synthesis = openai.format_synthesis(synthesis_results)
    
    # Generate YAML output
    print("Generating YAML output...")
    yaml_content = yaml_gen.generate_case_study(
        research_results,
        structured_synthesis,
        topic
    )
    
    # Save YAML to file
    output_filename = f"case_study_{topic.lower().replace(' ', '_')}.yaml"
    yaml_gen.save_to_file(yaml_content, output_filename)
    
    print(f"\nCase study generation complete!")
    print(f"Research stored in Notion (Page ID: {notion_page_id})")
    print(f"YAML output saved to: {output_filename}")

if __name__ == "__main__":
    main() 