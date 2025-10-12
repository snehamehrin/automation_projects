from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Section(BaseModel):
    """Represents a section in a case study."""
    title: str = Field(..., description="Title of the section")
    content: str = Field(default="", description="Content of the section")
    required: bool = Field(default=True, description="Whether this section is required")

class ResearchFinding(BaseModel):
    """Represents a research finding from Gemini."""
    prompt: str = Field(..., description="The prompt used for research")
    content: str = Field(..., description="The research content")
    timestamp: datetime = Field(default_factory=datetime.now)

class SynthesisResult(BaseModel):
    """Represents synthesis results from OpenAI."""
    key_themes: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class CaseStudy(BaseModel):
    """Represents a complete case study."""
    title: str = Field(..., description="Title of the case study")
    topic: str = Field(..., description="Main topic of the case study")
    date_generated: datetime = Field(default_factory=datetime.now)
    sections: Dict[str, Section] = Field(default_factory=dict)
    research_findings: List[ResearchFinding] = Field(default_factory=list)
    synthesis: Optional[SynthesisResult] = None

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "title": "Case Study: AI in Healthcare",
                "topic": "AI in Healthcare",
                "sections": {
                    "executive_summary": {
                        "title": "Executive Summary",
                        "content": "Overview of the case study..."
                    }
                }
            }
        } 