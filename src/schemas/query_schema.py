# src/schemas/query_schema.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from enum import Enum


class QueryType(str, Enum):
    """Types of queries the system can handle"""

    EXACT_MATCH = "EXACT_MATCH"  # Specific product numbers, SKUs
    ATTRIBUTE_FILTER = "ATTRIBUTE_FILTER"  # Filter by specifications (watt, hours, etc.)
    SEMANTIC = "SEMANTIC"  # Natural language queries
    HYBRID = "HYBRID"  # Combination of semantic + filters


class AttributeFilter(BaseModel):
    """Attribute-based filtering criteria"""

    watt_min: Optional[int] = Field(None, description="Minimum wattage")
    watt_max: Optional[int] = Field(None, description="Maximum wattage")

    lebensdauer_min: Optional[int] = Field(None, description="Minimum lifetime in hours")
    lebensdauer_max: Optional[int] = Field(None, description="Maximum lifetime in hours")

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
    language: str = Field(default="de", description="Detected language")


class SearchStrategy(BaseModel):
    """Search strategy configuration"""

    strategy_name: str = Field(..., description="Name of the search strategy")
    description: str = Field(..., description="Strategy description")

    # Search parameters
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    exact_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    # Result limits
    initial_candidates: int = Field(default=20, ge=1, le=100)
    final_results: int = Field(default=5, ge=1, le=20)

    # Reranking
    enable_reranking: bool = Field(default=True)
    rerank_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Additional parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
