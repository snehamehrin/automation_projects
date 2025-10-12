import re
from typing import Any, Dict, Optional

def validate_api_key(api_key: str) -> None:
    """Validate an API key.
    
    Args:
        api_key: The API key to validate
        
    Raises:
        ValueError: If the API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key must be a non-empty string")
    
    if len(api_key) < 10:  # Basic length check
        raise ValueError("API key appears to be invalid (too short)")

def validate_topic(topic: str) -> None:
    """Validate a research topic.
    
    Args:
        topic: The topic to validate
        
    Raises:
        ValueError: If the topic is invalid
    """
    if not topic or not isinstance(topic, str):
        raise ValueError("Topic must be a non-empty string")
    
    if len(topic) < 3:
        raise ValueError("Topic must be at least 3 characters long")
    
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', topic):
        raise ValueError("Topic contains invalid characters")

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary.
    
    Args:
        config: The configuration to validate
        
    Raises:
        ValueError: If the configuration is invalid
    """
    required_keys = ['case_study_template', 'research_prompts', 'synthesis_prompts']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    if not isinstance(config['case_study_template'], dict):
        raise ValueError("case_study_template must be a dictionary")
    
    if 'sections' not in config['case_study_template']:
        raise ValueError("case_study_template must contain 'sections'")

def validate_yaml_content(content: str) -> None:
    """Validate YAML content.
    
    Args:
        content: The YAML content to validate
        
    Raises:
        ValueError: If the content is invalid
    """
    if not content or not isinstance(content, str):
        raise ValueError("YAML content must be a non-empty string")
    
    # Basic YAML structure validation
    if not content.strip().startswith('case_study:'):
        raise ValueError("YAML content must start with 'case_study:'") 