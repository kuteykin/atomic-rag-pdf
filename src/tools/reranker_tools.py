# src/tools/reranker_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from sentence_transformers import CrossEncoder
from pydantic import Field
from typing import List, Dict, Any
from src.config.constants import DEFAULT_RERANK_MODEL


class RerankerToolConfig(BaseToolConfig):
    model_name: str = Field(
        default=DEFAULT_RERANK_MODEL,
        description="Cross-encoder model for reranking",
    )


class RerankerTool(BaseTool):
    """Tool for reranking search results by relevance"""

    def __init__(self, config: RerankerToolConfig = None):
        super().__init__(config or RerankerToolConfig())
        self.model = CrossEncoder(self.config.model_name)

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank documents by relevance to query"""

        # Prepare pairs for cross-encoder
        pairs = []
        for doc in documents:
            text = doc.get("text", "") or doc.get("full_description", "")
            pairs.append([query, text])

        # Score pairs
        scores = self.model.predict(pairs)

        # Combine scores with documents
        scored_docs = []
        for i, doc in enumerate(documents):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(scores[i])
            scored_docs.append(doc_copy)

        # Sort by score
        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        return scored_docs[:top_k]

    def run(self, query: str, documents: List[Dict[str, Any]] = None, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Required by BaseTool - reranks documents"""
        if documents:
            return {"reranked_documents": self.rerank(query, documents, top_k)}
        else:
            return {"message": "No documents provided for reranking"}
