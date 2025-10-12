from typing import Dict, List
from pydantic import BaseModel, Field

class TemplateSection(BaseModel):
    """Configuration for a case study section."""
    title: str = Field(..., description="Title of the section")
    description: str = Field(..., description="Description of the section")
    required: bool = Field(default=True, description="Whether this section is required")

class ResearchPrompts(BaseModel):
    """Configuration for research prompts."""
    gemini: List[str] = Field(default_factory=list, description="Prompts for Gemini research")

class SynthesisPrompts(BaseModel):
    """Configuration for synthesis prompts."""
    openai: List[str] = Field(default_factory=list, description="Prompts for OpenAI synthesis")

class OutputFormat(BaseModel):
    """Configuration for output formatting."""
    yaml: Dict[str, bool] = Field(
        default={"indent": True, "sort_keys": True},
        description="YAML output formatting options"
    )

class CaseStudyConfig(BaseModel):
    """Main configuration model."""
    case_study_template: Dict[str, List[TemplateSection]] = Field(
        ...,
        description="Template configuration for case studies"
    )
    research_prompts: ResearchPrompts = Field(
        default_factory=ResearchPrompts,
        description="Research prompt configurations"
    )
    synthesis_prompts: SynthesisPrompts = Field(
        default_factory=SynthesisPrompts,
        description="Synthesis prompt configurations"
    )
    output_format: OutputFormat = Field(
        default_factory=OutputFormat,
        description="Output formatting configurations"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "case_study_template": {
                    "sections": [
                        {
                            "title": "Executive Summary",
                            "description": "Brief overview of the case study",
                            "required": True
                        }
                    ]
                }
            }
        } 