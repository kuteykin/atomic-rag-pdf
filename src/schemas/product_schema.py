# src/schemas/product_schema.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProductSpecification(BaseModel):
    """Product specification data extracted from PDFs"""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    # Basic identification
    product_name: str = Field(..., description="Product name/title")
    sku: str = Field(..., description="SKU or product code")
    primary_product_number: Optional[str] = Field(None, description="Primary product number")

    # Technical specifications
    watt: Optional[int] = Field(None, description="Power consumption in watts")
    voltage: Optional[str] = Field(None, description="Operating voltage")
    current: Optional[str] = Field(None, description="Current consumption")

    # Light characteristics
    color_temperature: Optional[str] = Field(
        None, description="Color temperature (e.g., 3000K, 4000K)"
    )
    color_rendering_index: Optional[int] = Field(None, description="CRI value")
    luminous_flux: Optional[int] = Field(None, description="Luminous flux in lumens")
    beam_angle: Optional[str] = Field(None, description="Beam angle")

    # Lifetime and durability
    lebensdauer_stunden: Optional[int] = Field(None, description="Lifetime in hours")
    operating_temperature: Optional[str] = Field(None, description="Operating temperature range")

    # Physical dimensions
    dimensions: Optional[str] = Field(None, description="Physical dimensions")
    weight: Optional[str] = Field(None, description="Weight")

    # Application and usage
    application_area: Optional[str] = Field(None, description="Recommended application area")
    suitable_for: Optional[List[str]] = Field(
        default_factory=list, description="Suitable environments"
    )

    # Additional specifications
    certifications: Optional[List[str]] = Field(default_factory=list, description="Certifications")
    ip_rating: Optional[str] = Field(None, description="IP protection rating")

    # Full description text
    full_description: str = Field(..., description="Complete product description text")

    # Metadata
    source_pdf: str = Field(..., description="Source PDF file path")
    extracted_at: datetime = Field(default_factory=datetime.now)


class ProductSearchResult(BaseModel):
    """Search result with relevance scoring"""

    product: ProductSpecification
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    rerank_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    search_strategy: str = Field(..., description="Search method used")
    source_chunk: Optional[str] = Field(None, description="Relevant text chunk")
