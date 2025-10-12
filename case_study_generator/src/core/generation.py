import logging
import yaml
from typing import Dict, Any, Optional
from src.core.research import ResearchOrchestrator
from src.core.synthesis import SynthesisOrchestrator
from src.models.case_study import CaseStudy, Section
from src.utils.validation import validate_config, validate_yaml_content
from src.utils.formatting import format_case_study_yaml

logger = logging.getLogger(__name__)

class CaseStudyGenerator:
    """Generates case studies from research and synthesis."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the case study generator.
        
        Args:
            config: Configuration dictionary
        """
        validate_config(config)
        self.config = config
        logger.info("Case study generator initialized")

    async def generate(
        self,
        topic: str,
        research_orchestrator: ResearchOrchestrator,
        synthesis_orchestrator: SynthesisOrchestrator
    ) -> CaseStudy:
        """Generate a case study.
        
        Args:
            topic: The topic to generate a case study for
            research_orchestrator: Initialized research orchestrator
            synthesis_orchestrator: Initialized synthesis orchestrator
            
        Returns:
            Generated case study
            
        Raises:
            RuntimeError: If generation process fails
        """
        try:
            logger.info(f"Starting case study generation for topic: {topic}")
            
            # Conduct research
            findings, notion_page_id = await research_orchestrator.conduct_research(topic)
            
            # Validate findings
            if not await research_orchestrator.validate_findings(findings):
                raise RuntimeError("Research findings validation failed")
            
            # Synthesize content
            synthesis = await synthesis_orchestrator.synthesize_content(
                "\n".join(f.content for f in findings)
            )
            
            # Validate synthesis
            if not await synthesis_orchestrator.validate_synthesis(synthesis):
                raise RuntimeError("Synthesis validation failed")
            
            # Create case study
            case_study = CaseStudy(
                title=f"Case Study: {topic}",
                topic=topic,
                sections=self._create_sections(),
                research_findings=findings,
                synthesis=synthesis
            )
            
            logger.info("Case study generation completed successfully")
            return case_study
            
        except Exception as e:
            logger.error(f"Case study generation failed: {str(e)}")
            raise RuntimeError(f"Case study generation failed: {str(e)}")

    def save_to_yaml(self, case_study: CaseStudy, filename: str) -> None:
        """Save case study to YAML file.
        
        Args:
            case_study: Case study to save
            filename: Output filename
            
        Raises:
            RuntimeError: If saving fails
        """
        try:
            yaml_content = format_case_study_yaml(case_study.dict())
            validate_yaml_content(yaml_content)
            
            with open(filename, 'w') as f:
                f.write(yaml_content)
                
            logger.info(f"Case study saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save case study: {str(e)}")
            raise RuntimeError(f"Failed to save case study: {str(e)}")

    def _create_sections(self) -> Dict[str, Section]:
        """Create sections from template.
        
        Returns:
            Dictionary of sections
        """
        sections = {}
        for section in self.config['case_study_template']['sections']:
            section_title = section['title'].lower().replace(" ", "_")
            sections[section_title] = Section(
                title=section['title'],
                content="",
                required=section['required']
            )
        return sections 