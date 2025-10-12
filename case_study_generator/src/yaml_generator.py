import yaml
from datetime import datetime

class YAMLGenerator:
    def __init__(self, template_config: dict):
        self.template = template_config

    def generate_case_study(self, research_data: dict, synthesis_data: dict, topic: str) -> str:
        """
        Generate a case study in YAML format.
        
        Args:
            research_data (dict): Research results
            synthesis_data (dict): Synthesized themes and insights
            topic (str): Case study topic
            
        Returns:
            str: YAML formatted case study
        """
        case_study = {
            "case_study": {
                "title": f"Case Study: {topic}",
                "date_generated": datetime.now().strftime("%Y-%m-%d"),
                "sections": {}
            }
        }

        # Add template sections
        for section in self.template['case_study_template']['sections']:
            section_title = section['title'].lower().replace(" ", "_")
            case_study['case_study']['sections'][section_title] = {
                "title": section['title'],
                "content": ""
            }

        # Add research findings
        case_study['case_study']['research_findings'] = research_data

        # Add synthesis results
        case_study['case_study']['synthesis'] = synthesis_data

        # Convert to YAML
        yaml_output = yaml.dump(
            case_study,
            sort_keys=False,
            indent=2,
            default_flow_style=False
        )

        return yaml_output

    def save_to_file(self, yaml_content: str, filename: str) -> None:
        """
        Save YAML content to a file.
        
        Args:
            yaml_content (str): YAML formatted content
            filename (str): Output filename
        """
        with open(filename, 'w') as f:
            f.write(yaml_content) 