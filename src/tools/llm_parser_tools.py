# src/tools/llm_parser_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List
import logging
from mistralai import Mistral
from src.schemas.product_schema import ProductSpecification
import json

logger = logging.getLogger(__name__)


class LLMParserToolConfig(BaseToolConfig):
    """Configuration for LLM parser tool"""

    api_key: str = Field(..., description="Mistral API key")
    model: str = Field(default="mistral-large-latest", description="LLM model for parsing")


class LLMParserTool(BaseTool):
    """Tool for parsing structured product data from OCR text using LLM"""

    def __init__(self, config: LLMParserToolConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.client = Mistral(api_key=self.api_key)

    def run(self, text: str, source_pdf: str = "unknown.pdf") -> List[ProductSpecification]:
        """Parse text and extract product specifications using LLM"""
        try:
            # Get database schema information
            schema_info = self._get_schema_info()

            # Create the parsing prompt
            prompt = self._create_parsing_prompt(text, schema_info)

            # Call LLM for parsing
            logger.info(f"Parsing text with LLM (model: {self.model})")
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured product information from technical datasheets. Extract data accurately and return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"},
            )

            # Parse the LLM response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # Convert to ProductSpecification objects
            products = []
            for product_data in result.get("products", []):
                # Add source_pdf and full_description
                product_data["source_pdf"] = source_pdf
                product_data["full_description"] = text

                # Ensure required fields have defaults
                if not product_data.get("product_name"):
                    product_data["product_name"] = "Unknown Product"
                if not product_data.get("sku"):
                    # Try to extract from filename
                    product_data["sku"] = self._extract_sku_from_filename(source_pdf)

                try:
                    product = ProductSpecification(**product_data)
                    products.append(product)
                except Exception as e:
                    logger.error(f"Error creating ProductSpecification: {e}")
                    logger.debug(f"Product data: {product_data}")

            logger.info(f"Successfully parsed {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Error parsing text with LLM: {e}")
            return []

    def _get_schema_info(self) -> dict:
        """Get database schema information dynamically from ProductSpecification"""
        from src.utils.schema_utils import SchemaIntrospector

        # Get schema from ProductSpecification model
        schema_info = SchemaIntrospector.get_schema_info(ProductSpecification)

        # Add priority/special instructions for critical fields
        for field in schema_info["required_fields"]:
            if field["name"] == "product_name":
                field["priority"] = (
                    "CRITICAL - Extract from: 1) Global order reference in table, "
                    "2) Main heading (skip 'Product datasheet', images, and generic headers), "
                    "3) Product name (Americas) field"
                )
                field["description"] = (
                    "The official product name or model number (e.g., 'SIRIUS HRI 420 W'). "
                    "Look for this in the title, header, or 'Global order reference' field in tables. "
                    "NEVER use generic headers like 'Product datasheet' or bullet points as the product name."
                )
            elif field["name"] == "sku":
                field["priority"] = "CRITICAL"
                field["description"] = (
                    "SKU or product code (e.g., 'ZMP_12345', '64674'). "
                    "Can be found in Product code, Article number, Item number, or similar fields."
                )

        return schema_info

    def _create_parsing_prompt(self, text: str, schema_info: dict) -> str:
        """Create the parsing prompt for the LLM"""

        required_fields_desc = "\n".join(
            [
                f"- **{field['name']}** ({field['type']}): {field['description']}"
                + (f"\n  PRIORITY: {field['priority']}" if "priority" in field else "")
                for field in schema_info["required_fields"]
            ]
        )

        optional_fields_desc = "\n".join(
            [
                f"- {field['name']} ({field['type']}): {field['description']}"
                for field in schema_info["optional_fields"]
            ]
        )

        prompt = f"""Extract structured product information from the following technical datasheet text.

**CRITICAL INSTRUCTIONS FOR PRODUCT NAME:**
1. FIRST, look for "Global order reference" in any tables - this is the most reliable source
2. If not found, look for the main product heading (must be an actual product model/name)
3. SKIP these types of content:
   - Generic headers like "Product datasheet", "Technical specification"
   - Image references like "![img-0.jpeg](img-0.jpeg)"
   - Bullet points or product features (e.g., "- Lightweight and compact...")
   - Section headers like "Areas of application"
4. The product name should be a specific model identifier like "SIRIUS HRI 420 W S" or "64674 HLX"

**Database Schema - Required Fields (MUST extract):**
{required_fields_desc}

**Optional Fields (extract if available):**
{optional_fields_desc}

**Input Text:**
```
{text}
```

**Output Format:**
Return a JSON object with this structure:
{{
  "products": [
    {{
      "product_name": "exact product name",
      "sku": "product code",
      "primary_product_number": "...",
      "wattage": numeric_value,
      "voltage": "...",
      ... (other fields)
    }}
  ]
}}

**Important Rules:**
1. Extract ONLY information explicitly present in the text
2. Use null for missing optional fields
3. Convert numeric fields (wattage, luminous_flux, etc.) to integers without units
4. For arrays (suitable_for, certifications), return empty arrays [] if no data
5. Be precise and accurate - do not hallucinate or infer data
6. If multiple products are described, include all in the "products" array
7. For the product_name, ALWAYS check "Global order reference" field first

Return ONLY the JSON object, no additional text."""

        return prompt

    def _extract_sku_from_filename(self, filename: str) -> str:
        """Extract SKU from filename as fallback"""
        import re
        import os

        basename = os.path.basename(filename)

        # Try to extract ZMP codes
        zmp_match = re.search(r"ZMP[_\s]*(\d+)", basename)
        if zmp_match:
            return f"ZMP_{zmp_match.group(1)}"

        # Try to extract any alphanumeric code
        code_match = re.search(r"([A-Z0-9]+)", basename)
        if code_match:
            return code_match.group(1)

        return "UNKNOWN_SKU"
