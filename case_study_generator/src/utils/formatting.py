import yaml
from typing import Dict, Any
from datetime import datetime

def format_research_for_notion(research_findings: Dict[str, str]) -> str:
    """Format research findings for Notion storage.
    
    Args:
        research_findings: Dictionary of research findings
        
    Returns:
        Formatted markdown text
    """
    formatted_text = "# Research Results\n\n"
    
    for prompt, content in research_findings.items():
        formatted_text += f"## {prompt}\n\n{content}\n\n"
    
    return formatted_text

def format_case_study_yaml(case_study: Dict[str, Any]) -> str:
    """Format case study data as YAML.
    
    Args:
        case_study: Case study data dictionary
        
    Returns:
        YAML formatted string
    """
    # Add metadata
    case_study['metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    # Convert to YAML
    yaml_content = yaml.dump(
        case_study,
        sort_keys=False,
        indent=2,
        default_flow_style=False,
        allow_unicode=True
    )
    
    return yaml_content

def format_synthesis_for_yaml(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """Format synthesis results for YAML output.
    
    Args:
        synthesis: Raw synthesis results
        
    Returns:
        Formatted synthesis data
    """
    formatted = {
        'key_themes': [],
        'insights': [],
        'recommendations': []
    }
    
    for category, items in synthesis.items():
        if isinstance(items, list):
            formatted[category] = [
                item.strip() for item in items if item.strip()
            ]
        else:
            formatted[category] = [items.strip()]
    
    return formatted 