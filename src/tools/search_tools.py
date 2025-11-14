# src/tools/search_tools.py

"""
Search tools for the RAG system - language-agnostic search functionality
Query classification is handled by LLMQueryClassifier for multilingual support
"""

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List, Dict, Any, Optional
import logging
from src.schemas.query_schema import AttributeFilter
from src.tools.storage_tools import SQLiteStorageTool, QdrantStorageTool, EmbeddingTool
from src.tools.storage_tools import (
    SQLiteStorageToolConfig,
    QdrantStorageToolConfig,
    EmbeddingToolConfig,
)
from src.config.constants import DEFAULT_SQLITE_PATH, DEFAULT_QDRANT_PATH, DEFAULT_COLLECTION_NAME

logger = logging.getLogger(__name__)


class SQLiteSearchToolConfig(BaseToolConfig):
    """Configuration for SQLite search tool"""

    db_path: str = Field(default=DEFAULT_SQLITE_PATH)


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

    qdrant_path: str = Field(default=DEFAULT_QDRANT_PATH)
    collection_name: str = Field(default=DEFAULT_COLLECTION_NAME)


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
                    "wattage": payload.get("wattage"),
                    "lifetime_hours": payload.get("lifetime_hours"),
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

    sqlite_path: str = Field(default=DEFAULT_SQLITE_PATH)
    qdrant_path: str = Field(default=DEFAULT_QDRANT_PATH)
    collection_name: str = Field(default=DEFAULT_COLLECTION_NAME)


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
