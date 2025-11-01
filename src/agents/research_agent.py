# src/agents/research_agent.py

from src.lib.base_agent import BaseAgent, BaseAgentConfig
from pydantic import Field
from typing import Literal
from src.config.constants import (
    DEFAULT_SQLITE_PATH,
    DEFAULT_QDRANT_PATH,
    DEFAULT_RERANK_TOP_K,
    DEFAULT_FINAL_TOP_K,
)


class ResearchAgentConfig(BaseAgentConfig):
    """Configuration for Research Agent"""

    sqlite_path: str = Field(default=DEFAULT_SQLITE_PATH)
    qdrant_path: str = Field(default=DEFAULT_QDRANT_PATH)
    rerank_top_k: int = Field(default=DEFAULT_RERANK_TOP_K)
    final_top_k: int = Field(default=DEFAULT_FINAL_TOP_K)


class ResearchAgent(BaseAgent):
    """
    Agent responsible for:
    1. Classifying query type (semantic vs exact vs hybrid)
    2. Executing appropriate search strategy
    3. Reranking results for relevance
    4. Returning top-k results with context
    """

    def __init__(self, config: ResearchAgentConfig):
        from src.tools.search_tools import (
            SQLiteSearchTool,
            SQLiteSearchToolConfig,
            QdrantSearchTool,
            QdrantSearchToolConfig,
            HybridSearchTool,
            HybridSearchToolConfig,
        )
        from src.tools.llm_query_classifier import LLMQueryClassifier, LLMQueryClassifierConfig
        from src.tools.reranker_tools import RerankerTool, RerankerToolConfig
        from src.tools.translation_tools import TranslationTool, TranslationToolConfig
        from src.config.settings import settings

        # Initialize tools
        self.classifier_tool = LLMQueryClassifier(
            LLMQueryClassifierConfig(api_key=settings.mistral_api_key, model=settings.llm_model)
        )
        self.sqlite_tool = SQLiteSearchTool(SQLiteSearchToolConfig(db_path=config.sqlite_path))
        self.qdrant_tool = QdrantSearchTool(QdrantSearchToolConfig(qdrant_path=config.qdrant_path))
        self.hybrid_tool = HybridSearchTool(
            HybridSearchToolConfig(sqlite_path=config.sqlite_path, qdrant_path=config.qdrant_path)
        )
        self.reranker_tool = RerankerTool(RerankerToolConfig())
        self.translation_tool = TranslationTool(
            TranslationToolConfig(api_key=settings.mistral_api_key)
        )

        # Initialize base agent
        super().__init__(config)

    def search(self, query: str) -> dict:
        """Execute intelligent search based on query type with translation support"""

        # Step 1: Translate query to English if needed
        translation_info = self.translation_tool.translate_query(query)
        english_query = translation_info["english_query"]
        detected_language = translation_info["detected_language"]

        print(f"Query language detected: {detected_language}")
        if translation_info["translation_needed"]:
            print(f"Translated query: {english_query}")

        # Step 2: Classify query
        classification = self.classifier_tool.classify(english_query)
        query_type = classification.type

        print(f"Query classified as: {query_type}")

        # Step 3: Execute appropriate search
        if query_type == "EXACT_MATCH":
            # e.g., "Erzeugnisnummer 4062172212311"
            results = self.sqlite_tool.exact_search(english_query)

        elif query_type == "ATTRIBUTE_FILTER":
            # e.g., "≥1000W und >400h"
            filters = classification.filters
            if filters:
                results = self.sqlite_tool.filter_search(filters)
            else:
                results = []

        elif query_type == "SEMANTIC":
            # e.g., "gut für Operationssaal"
            results = self.qdrant_tool.semantic_search(
                query=english_query, top_k=self.config.rerank_top_k
            )

        elif query_type == "HYBRID":
            # e.g., "energy-efficient Leuchtmittel >1000W"
            filters = classification.filters
            results = self.hybrid_tool.hybrid_search(
                query=english_query,
                filters=filters,
                top_k=self.config.rerank_top_k,
            )

        else:
            # Fallback to semantic search
            results = self.qdrant_tool.semantic_search(
                query=english_query, top_k=self.config.rerank_top_k
            )

        # Step 4: Rerank results
        if len(results) > self.config.final_top_k:
            reranked_results = self.reranker_tool.rerank(
                query=english_query, documents=results, top_k=self.config.final_top_k
            )
        else:
            reranked_results = results

        # Step 5: Translate results back to original language if needed
        if translation_info["translation_needed"]:
            reranked_results = self.translation_tool.translate_results(
                reranked_results, detected_language
            )

        return {
            "query": query,
            "english_query": english_query,
            "query_type": query_type,
            "detected_language": detected_language,
            "translation_needed": translation_info["translation_needed"],
            "total_results": len(results),
            "top_results": reranked_results[: self.config.final_top_k],
            "search_strategy": query_type,
        }

    def process(self, query: str, **kwargs) -> dict:
        """Required by BaseAgent - processes search queries"""
        return self.search(query)
