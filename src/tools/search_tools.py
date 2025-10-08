# src/tools/search_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List, Dict, Any, Optional
import re
import logging
from src.schemas.query_schema import QueryClassification, QueryType, AttributeFilter
from src.tools.storage_tools import SQLiteStorageTool, QdrantStorageTool, EmbeddingTool
from src.tools.storage_tools import (
    SQLiteStorageToolConfig,
    QdrantStorageToolConfig,
    EmbeddingToolConfig,
)

logger = logging.getLogger(__name__)


class QueryClassifierToolConfig(BaseToolConfig):
    """Configuration for query classifier tool"""

    pass


class QueryClassifierTool(BaseTool):
    """Tool for classifying query types"""

    def __init__(self, config: QueryClassifierToolConfig = None):
        super().__init__(config or QueryClassifierToolConfig())

    def classify(self, query: str) -> QueryClassification:
        """Classify the query type"""
        try:
            query_lower = query.lower()

            # Check for exact match patterns
            if self._is_exact_match(query):
                return QueryClassification(
                    query=query,
                    type=QueryType.EXACT_MATCH,
                    confidence=0.9,
                    keywords=self._extract_keywords(query),
                )

            # Check for attribute filter patterns
            filters = self._extract_filters(query)
            if filters and self._has_filter_indicators(query):
                return QueryClassification(
                    query=query,
                    type=QueryType.ATTRIBUTE_FILTER,
                    confidence=0.8,
                    filters=filters,
                    keywords=self._extract_keywords(query),
                )

            # Check for hybrid patterns (semantic + filters)
            if filters and self._has_semantic_indicators(query):
                return QueryClassification(
                    query=query,
                    type=QueryType.HYBRID,
                    confidence=0.7,
                    filters=filters,
                    keywords=self._extract_keywords(query),
                )

            # Default to semantic search
            return QueryClassification(
                query=query,
                type=QueryType.SEMANTIC,
                confidence=0.6,
                keywords=self._extract_keywords(query),
            )

        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return QueryClassification(
                query=query, type=QueryType.SEMANTIC, confidence=0.5, keywords=[]
            )

    def _is_exact_match(self, query: str) -> bool:
        """Check if query is looking for exact match"""
        exact_patterns = [
            r"erzeugnisnummer\s+\d+",
            r"primäre\s+erzeugnisnummer\s+\d+",
            r"sku\s+[A-Z0-9\-/]+",
            r"artikel\s+[A-Z0-9\-/]+",
            r"produktnummer\s+\d+",
        ]

        for pattern in exact_patterns:
            if re.search(pattern, query.lower()):
                return True

        return False

    def _has_filter_indicators(self, query: str) -> bool:
        """Check if query has filter indicators"""
        filter_indicators = [
            "mindestens",
            "mind.",
            "min.",
            "ab",
            "über",
            "mehr als",
            "maximal",
            "max.",
            "bis",
            "unter",
            "weniger als",
            "zwischen",
            "von",
            "bis",
            "watt",
            "stunden",
            "lebensdauer",
            "betriebsdauer",
            "farbtemperatur",
            "kelvin",
            "k",
            "ip",
            "schutzart",
            "zertifizierung",
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in filter_indicators)

    def _has_semantic_indicators(self, query: str) -> bool:
        """Check if query has semantic indicators"""
        semantic_indicators = [
            "gut für",
            "geeignet für",
            "empfohlen für",
            "operationssaal",
            "op",
            "krankenhaus",
            "klinik",
            "büro",
            "wohnung",
            "industrie",
            "außenbereich",
            "energiesparend",
            "effizient",
            "modern",
            "welche",
            "was",
            "wie",
            "empfehlung",
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in semantic_indicators)

    def _extract_filters(self, query: str) -> Optional[AttributeFilter]:
        """Extract attribute filters from query"""
        filters = AttributeFilter()

        # Extract wattage filters
        watt_patterns = [
            r"mindestens\s+(\d+)\s*watt",
            r"mind\.\s+(\d+)\s*watt",
            r"min\.\s+(\d+)\s*watt",
            r"ab\s+(\d+)\s*watt",
            r"über\s+(\d+)\s*watt",
            r"mehr\s+als\s+(\d+)\s*watt",
            r"(\d+)\s*watt\s+und\s+mehr",
        ]

        for pattern in watt_patterns:
            match = re.search(pattern, query.lower())
            if match:
                filters.watt_min = int(match.group(1))
                break

        # Extract lifetime filters
        lifetime_patterns = [
            r"mindestens\s+(\d+)\s*stunden",
            r"mind\.\s+(\d+)\s*stunden",
            r"min\.\s+(\d+)\s*stunden",
            r"ab\s+(\d+)\s*stunden",
            r"über\s+(\d+)\s*stunden",
            r"mehr\s+als\s+(\d+)\s*stunden",
            r"(\d+)\s*stunden\s+und\s+mehr",
        ]

        for pattern in lifetime_patterns:
            match = re.search(pattern, query.lower())
            if match:
                filters.lebensdauer_min = int(match.group(1))
                break

        # Extract color temperature
        color_temp_patterns = [
            r"(\d+)\s*k(?:elvin)?",
            r"farbtemperatur\s+(\d+)\s*k",
        ]

        for pattern in color_temp_patterns:
            match = re.search(pattern, query.lower())
            if match:
                filters.color_temperature = match.group(1) + "K"
                break

        # Extract application area
        application_patterns = [
            r"für\s+([^.\n]+?)(?:\s+geeignet|\s+empfohlen|\s+geeignet)",
            r"geeignet\s+für\s+([^.\n]+)",
            r"empfohlen\s+für\s+([^.\n]+)",
        ]

        for pattern in application_patterns:
            match = re.search(pattern, query.lower())
            if match:
                filters.application_area = match.group(1).strip()
                break

        # Check if any filters were found
        if any(
            [
                filters.watt_min,
                filters.watt_max,
                filters.lebensdauer_min,
                filters.lebensdauer_max,
                filters.color_temperature,
                filters.application_area,
                filters.ip_rating,
                filters.certifications,
            ]
        ):
            return filters

        return None

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Remove common German stop words
        stop_words = {
            "der",
            "die",
            "das",
            "den",
            "dem",
            "des",
            "ein",
            "eine",
            "einen",
            "einem",
            "eines",
            "und",
            "oder",
            "aber",
            "mit",
            "für",
            "von",
            "zu",
            "in",
            "auf",
            "an",
            "bei",
            "ist",
            "sind",
            "war",
            "waren",
            "wird",
            "werden",
            "hat",
            "haben",
            "hatte",
            "hatten",
            "kann",
            "können",
            "soll",
            "sollen",
            "muss",
            "müssen",
            "darf",
            "dürfen",
            "was",
            "wer",
            "wie",
            "wo",
            "wann",
            "warum",
            "welche",
            "welcher",
            "welches",
        }

        # Extract words
        words = re.findall(r"\b[a-zA-ZäöüßÄÖÜ]+\b", query.lower())

        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords

    def run(self, query: str, **kwargs) -> dict:
        """Required by BaseTool - classifies queries"""
        classification = self.classify(query)
        return classification.dict()


class SQLiteSearchToolConfig(BaseToolConfig):
    """Configuration for SQLite search tool"""

    db_path: str = Field(default="./storage/products.db")


class SQLiteSearchTool(BaseTool):
    """Tool for searching SQLite database"""

    def __init__(self, config: SQLiteSearchToolConfig):
        super().__init__(config)
        self.sqlite_tool = SQLiteStorageTool(SQLiteStorageToolConfig(db_path=config.db_path))

    def exact_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform exact search"""
        return self.sqlite_tool.search_exact(query)

    def filter_search(self, filters: AttributeFilter) -> List[Dict[str, Any]]:
        """Perform filter search"""
        filter_dict = filters.dict(exclude_none=True)
        return self.sqlite_tool.search_by_filters(filter_dict)

    def run(self, query: str = "", filters: dict = None, **kwargs) -> dict:
        """Required by BaseTool - performs SQLite search"""
        if filters:
            return {"results": self.filter_search(AttributeFilter(**filters))}
        else:
            return {"results": self.exact_search(query)}


class QdrantSearchToolConfig(BaseToolConfig):
    """Configuration for Qdrant search tool"""

    qdrant_path: str = Field(default="./storage/qdrant_storage")
    collection_name: str = Field(default="products")


class QdrantSearchTool(BaseTool):
    """Tool for searching Qdrant vector database"""

    def __init__(self, config: QdrantSearchToolConfig):
        super().__init__(config)
        self.qdrant_tool = QdrantStorageTool(
            QdrantStorageToolConfig(
                qdrant_path=config.qdrant_path, collection_name=config.collection_name
            )
        )
        self.embedding_tool = EmbeddingTool()

    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_tool.generate(query)

            # Search in Qdrant
            results = self.qdrant_tool.search_similar(query_embedding, top_k)

            # Format results
            formatted_results = []
            for result in results:
                payload = result["payload"]
                formatted_result = {
                    "id": result["id"],
                    "score": result["score"],
                    "text": payload.get("text", ""),
                    "product_name": payload.get("product_name", ""),
                    "sku": payload.get("sku", ""),
                    "watt": payload.get("watt"),
                    "lebensdauer_stunden": payload.get("lebensdauer_stunden"),
                    "source_pdf": payload.get("source_pdf", ""),
                    "product_id": payload.get("product_id"),
                }
                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def run(self, query: str, top_k: int = 10, **kwargs) -> dict:
        """Required by BaseTool - performs semantic search"""
        return {"results": self.semantic_search(query, top_k)}


class HybridSearchToolConfig(BaseToolConfig):
    """Configuration for hybrid search tool"""

    sqlite_path: str = Field(default="./storage/products.db")
    qdrant_path: str = Field(default="./storage/qdrant_storage")
    collection_name: str = Field(default="products")


class HybridSearchTool(BaseTool):
    """Tool for hybrid search combining semantic and exact search"""

    def __init__(self, config: HybridSearchToolConfig):
        super().__init__(config)
        self.sqlite_tool = SQLiteSearchTool(SQLiteSearchToolConfig(db_path=config.sqlite_path))
        self.qdrant_tool = QdrantSearchTool(
            QdrantSearchToolConfig(
                qdrant_path=config.qdrant_path, collection_name=config.collection_name
            )
        )

    def hybrid_search(
        self, query: str, filters: Optional[AttributeFilter] = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search"""
        try:
            # Get semantic results
            semantic_results = self.qdrant_tool.semantic_search(query, top_k)

            # Get filter results if filters provided
            filter_results = []
            if filters:
                filter_results = self.sqlite_tool.filter_search(filters)

            # Combine and deduplicate results
            combined_results = self._combine_results(semantic_results, filter_results)

            return combined_results[:top_k]

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def _combine_results(
        self, semantic_results: List[Dict[str, Any]], filter_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate results"""
        # Create a map of results by product_id or sku
        result_map = {}

        # Add semantic results
        for result in semantic_results:
            key = result.get("product_id") or result.get("sku")
            if key:
                result["search_type"] = "semantic"
                result_map[key] = result

        # Add filter results, boosting existing semantic results
        for result in filter_results:
            key = result.get("id") or result.get("sku")
            if key in result_map:
                # Boost existing semantic result
                result_map[key]["search_type"] = "hybrid"
                result_map[key]["filter_match"] = True
            else:
                result["search_type"] = "filter"
                result_map[key] = result

        # Convert back to list and sort by score
        combined = list(result_map.values())
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)

        return combined

    def run(self, query: str, filters: dict = None, top_k: int = 10, **kwargs) -> dict:
        """Required by BaseTool - performs hybrid search"""
        filter_obj = AttributeFilter(**filters) if filters else None
        return {"results": self.hybrid_search(query, filter_obj, top_k)}
