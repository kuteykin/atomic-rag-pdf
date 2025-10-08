# src/schemas/answer_schema.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class Citation(BaseModel):
    """Citation for a factual claim"""

    claim: str = Field(..., description="The factual claim being cited")
    source: str = Field(..., description="Source product name/SKU")
    pdf_source: str = Field(..., description="Source PDF file")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Citation confidence")

    # Optional page reference if available
    page_number: Optional[int] = Field(None, description="Page number in PDF")


class AnswerValidation(BaseModel):
    """Validation results for generated answer"""

    completeness_score: float = Field(..., ge=0.0, le=1.0, description="How complete the answer is")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="How accurate the answer is")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")

    # Validation details
    missing_information: List[str] = Field(default_factory=list, description="Missing information")
    uncertain_claims: List[str] = Field(default_factory=list, description="Uncertain claims")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")

    # Fact-checking results
    verified_facts: int = Field(default=0, description="Number of verified facts")
    unverified_facts: int = Field(default=0, description="Number of unverified facts")

    # Source coverage
    sources_used: int = Field(default=0, description="Number of sources used")
    source_coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="Source coverage")


class GeneratedAnswer(BaseModel):
    """Complete answer with metadata"""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer text")

    # Quality scores
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    accuracy_score: float = Field(..., ge=0.0, le=1.0)

    # Citations and sources
    citations: List[Citation] = Field(default_factory=list)
    sources_used: int = Field(default=0, description="Number of sources used")

    # Warnings and limitations
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

    # Search metadata
    search_strategy: str = Field(..., description="Search strategy used")
    query_type: str = Field(..., description="Query type")
    total_results_found: int = Field(default=0, description="Total results found")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
