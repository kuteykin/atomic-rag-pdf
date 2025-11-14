# src/tools/llm_query_classifier.py

"""
LLM-based query classification tool
Replaces regex-based classification with intelligent LLM analysis
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from src.lib.base_tool import BaseTool, BaseToolConfig
from src.schemas.query_schema import QueryClassification, QueryType, AttributeFilter
from src.config.constants import DEFAULT_LLM_MODEL, DEFAULT_CLASSIFIER_TEMPERATURE

logger = logging.getLogger(__name__)


class LLMQueryClassifierConfig(BaseToolConfig):
    """Configuration for LLM-based query classifier"""

    api_key: str = Field(..., description="Mistral API key")
    model: str = Field(default=DEFAULT_LLM_MODEL, description="LLM model for classification")
    temperature: float = Field(
        default=DEFAULT_CLASSIFIER_TEMPERATURE,
        description="Temperature for classification (low for consistency)",
    )


class LLMQueryClassifier(BaseTool):
    """LLM-based query classification tool"""

    def __init__(self, config: LLMQueryClassifierConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.temperature = config.temperature

    def classify(self, query: str) -> QueryClassification:
        """Classify query using LLM analysis"""
        try:
            # Create classification prompt
            prompt = self._create_classification_prompt(query)

            # Call LLM
            response = self._call_llm(prompt)

            # Parse response
            classification_data = self._parse_llm_response(response)

            # Create QueryClassification object
            return self._create_classification(query, classification_data)

        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fallback to semantic search
            return QueryClassification(
                query=query,
                type=QueryType.SEMANTIC,
                confidence=0.5,
                keywords=self._extract_keywords_simple(query),
            )

    def _create_classification_prompt(self, query: str) -> str:
        """Create prompt for LLM classification - language agnostic"""
        prompt = f"""You are an expert query classifier for a multilingual product search system. Analyze the following query in ANY LANGUAGE and classify it into one of these categories:

**Query Types:**
1. **EXACT_MATCH**: Looking for a specific product by exact identifier
   - Product numbers, SKUs, article numbers
   - Examples: "4062172212311", "SKU ABC123", "Artikel-Nr. 12345"

2. **ATTRIBUTE_FILTER**: Filtering products by specific attributes/criteria
   - Numerical filters (wattage, lifetime, dimensions)
   - Categorical filters (color temperature, IP rating, certifications)
   - Examples: ">100W", "mindestens 1000 wattage", "IP65", "3000K"

3. **HYBRID**: Combination of semantic search + attribute filters
   - Descriptive queries with specific criteria
   - Examples: "LED lights >100W", "outdoor lights IP65", "warm white 3000K"

4. **SEMANTIC**: General descriptive or conceptual queries
   - Product recommendations, use cases, general descriptions
   - Examples: "lights for office", "energy efficient lighting", "hospital lighting"

**Query to classify:** "{query}"

**Instructions:**
1. Analyze the query intent in ANY LANGUAGE and classify it into ONE of the four types above
2. If the query contains specific numerical values or technical specifications, it's likely ATTRIBUTE_FILTER or HYBRID
3. If the query asks for a specific product identifier, it's EXACT_MATCH
4. If the query is purely descriptive without specific criteria, it's SEMANTIC
5. Extract any filters (wattage, lifetime, color temperature, etc.) as JSON - convert all values to English
6. Extract key keywords for search - translate to English for consistency
7. ALWAYS respond in English regardless of input language

**Response Format (JSON only):**
{{
    "type": "EXACT_MATCH|ATTRIBUTE_FILTER|HYBRID|SEMANTIC",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification",
    "filters": {{
        "wattage_min": null or number,
        "wattage_max": null or number,
        "lifetime_hours_min": null or number,
        "lifetime_hours_max": null or number,
        "color_temperature": null or string like "3000K",
        "application_area": null or string,
        "certifications": [],
        "ip_rating": null or string like "IP65"
    }},
    "keywords": ["keyword1", "keyword2", ...]
}}

**Example responses (multilingual):**
Query: "LED lights >100W" (English)
Response: {{"type": "HYBRID", "confidence": 0.9, "reasoning": "Combines semantic (LED lights) with wattage filter", "filters": {{"wattage_min": 100}}, "keywords": ["led", "lights"]}}

Query: "4062172212311" (Any language)
Response: {{"type": "EXACT_MATCH", "confidence": 0.95, "reasoning": "Specific product number", "filters": null, "keywords": []}}

Query: "Leuchten für Büro" (German)
Response: {{"type": "SEMANTIC", "confidence": 0.8, "reasoning": "General descriptive query", "filters": null, "keywords": ["lights", "office"]}}

Query: ">1000W und >400 Stunden" (German)
Response: {{"type": "ATTRIBUTE_FILTER", "confidence": 0.9, "reasoning": "Pure attribute filtering", "filters": {{"wattage_min": 1000, "lifetime_hours_min": 400}}, "keywords": []}}

Query: "Lumières LED >100W" (French)
Response: {{"type": "HYBRID", "confidence": 0.9, "reasoning": "Combines semantic (LED lights) with wattage filter", "filters": {{"wattage_min": 100}}, "keywords": ["led", "lights"]}}

**Now classify this query:**"""

        return prompt

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API"""
        import requests

        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": self.temperature,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                raise Exception(f"LLM API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Find JSON block if wrapped in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            required_fields = ["type", "confidence", "reasoning", "filters", "keywords"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response was: {response}")
            raise

    def _create_classification(self, query: str, data: Dict[str, Any]) -> QueryClassification:
        """Create QueryClassification object from parsed data"""
        try:
            # Map string type to QueryType enum
            type_mapping = {
                "EXACT_MATCH": QueryType.EXACT_MATCH,
                "ATTRIBUTE_FILTER": QueryType.ATTRIBUTE_FILTER,
                "HYBRID": QueryType.HYBRID,
                "SEMANTIC": QueryType.SEMANTIC,
            }

            query_type = type_mapping.get(data["type"], QueryType.SEMANTIC)

            # Create AttributeFilter if filters exist
            filters = None
            if data.get("filters") and any(v is not None for v in data["filters"].values()):
                try:
                    filters = AttributeFilter(**data["filters"])
                except Exception as e:
                    logger.warning(f"Error creating AttributeFilter: {e}")
                    filters = None

            return QueryClassification(
                query=query,
                type=query_type,
                confidence=data["confidence"],
                filters=filters,
                keywords=data.get("keywords", []),
            )

        except Exception as e:
            logger.error(f"Error creating classification: {e}")
            raise

    def _extract_keywords_simple(self, query: str) -> List[str]:
        """Simple keyword extraction fallback"""
        import re

        # Basic keyword extraction
        words = re.findall(r"\b\w+\b", query.lower())
        stop_words = {
            "der",
            "die",
            "das",
            "und",
            "oder",
            "mit",
            "für",
            "von",
            "zu",
            "auf",
            "in",
            "an",
            "bei",
            "the",
            "and",
            "or",
            "with",
            "for",
            "of",
            "to",
            "on",
            "in",
            "at",
            "by",
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Limit to 10 keywords

    def run(self, query: str, **kwargs) -> dict:
        """Required by BaseTool - classifies queries"""
        classification = self.classify(query)
        return classification.dict()
