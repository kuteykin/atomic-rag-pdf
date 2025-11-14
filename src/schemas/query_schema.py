# src/schemas/query_schema.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from enum import Enum
from src.config.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_SEMANTIC_WEIGHT,
    DEFAULT_EXACT_WEIGHT,
    DEFAULT_INITIAL_CANDIDATES,
    DEFAULT_FINAL_TOP_K,
    DEFAULT_ENABLE_RERANKING,
    DEFAULT_RERANK_MODEL,
)


class QueryType(str, Enum):
    """Types of queries the system can handle"""

    EXACT_MATCH = "EXACT_MATCH"  # Specific product numbers, SKUs
    ATTRIBUTE_FILTER = "ATTRIBUTE_FILTER"  # Filter by specifications (wattage, hours, etc.)
    SEMANTIC = "SEMANTIC"  # Natural language queries
    HYBRID = "HYBRID"  # Combination of semantic + filters


class AttributeFilter(BaseModel):
    """Attribute-based filtering criteria"""

    wattage_min: Optional[int] = Field(None, description="Minimum wattage")
    wattage_max: Optional[int] = Field(None, description="Maximum wattage")

    lifetime_hours_min: Optional[int] = Field(None, description="Minimum lifetime in hours")
    lifetime_hours_max: Optional[int] = Field(None, description="Maximum lifetime in hours")

    color_temperature: Optional[str] = Field(None, description="Specific color temperature")

    application_area: Optional[str] = Field(None, description="Application area filter")

    certifications: Optional[List[str]] = Field(
        default_factory=list, description="Required certifications"
    )

    ip_rating: Optional[str] = Field(None, description="IP rating filter")


class QueryClassification(BaseModel):
    """Result of query classification"""

    query: str = Field(..., description="Original query")
    type: QueryType = Field(..., description="Classified query type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")

    # Extracted filters for ATTRIBUTE_FILTER and HYBRID queries
    filters: Optional[AttributeFilter] = Field(None, description="Extracted attribute filters")

    # Keywords for semantic search
    keywords: Optional[List[str]] = Field(default_factory=list, description="Extracted keywords")

    # Intent analysis
    intent: Optional[str] = Field(None, description="User intent (find_product, compare, etc.)")

    # Language detection
    language: str = Field(default=DEFAULT_LANGUAGE, description="Detected language")


class SearchStrategy(BaseModel):
    """Search strategy configuration"""

    strategy_name: str = Field(..., description="Name of the search strategy")
    description: str = Field(..., description="Strategy description")

    # Search parameters
    semantic_weight: float = Field(default=DEFAULT_SEMANTIC_WEIGHT, ge=0.0, le=1.0)
    exact_weight: float = Field(default=DEFAULT_EXACT_WEIGHT, ge=0.0, le=1.0)

    # Result limits
    initial_candidates: int = Field(default=DEFAULT_INITIAL_CANDIDATES, ge=1, le=100)
    final_results: int = Field(default=DEFAULT_FINAL_TOP_K, ge=1, le=20)

    # Reranking
    enable_reranking: bool = Field(default=DEFAULT_ENABLE_RERANKING)
    rerank_model: str = Field(default=DEFAULT_RERANK_MODEL)

    # Additional parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
