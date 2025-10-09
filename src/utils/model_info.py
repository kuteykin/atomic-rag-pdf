# src/utils/model_info.py

"""
Utility functions to get actual model information used by the system
"""

import logging
from typing import Dict, Any, Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)


def get_actual_model_info() -> Dict[str, Any]:
    """
    Get the actual model information being used by the system
    Returns a dictionary with model details
    """
    model_info = {
        "llm": {
            "configured": settings.llm_model,
            "actual": None,
            "description": "Large Language Model for answer generation and translation",
        },
        "ocr": {
            "configured": settings.ocr_model,
            "actual": None,
            "description": "OCR model for PDF text extraction",
        },
        "embedding": {
            "configured": settings.embedding_model,
            "actual": None,
            "description": "Embedding model for vector search",
        },
        "reranker": {
            "configured": settings.rerank_model,
            "actual": None,
            "description": "Reranking model for result relevance scoring",
        },
    }

    try:
        # Get actual LLM model (from QA agent configuration)
        model_info["llm"]["actual"] = settings.llm_model

        # Get actual OCR model (from OCR tool)
        model_info["ocr"]["actual"] = settings.ocr_model

        # Get actual embedding model (from embedding manager)
        try:
            from src.utils.embedding_manager import EmbeddingManager

            embedding_manager = EmbeddingManager(settings.embedding_model)
            model_info["embedding"]["actual"] = embedding_manager.model_name
            model_info["embedding"]["dimension"] = embedding_manager.get_embedding_dimension()
        except Exception as e:
            logger.warning(f"Could not get embedding model info: {e}")
            model_info["embedding"]["actual"] = settings.embedding_model

        # Get actual reranker model
        model_info["reranker"]["actual"] = settings.rerank_model

        # Add additional model details
        model_info["llm"]["provider"] = "Mistral AI"
        model_info["ocr"]["provider"] = "Mistral AI"
        model_info["embedding"]["provider"] = "Sentence Transformers"
        model_info["reranker"]["provider"] = "Cross Encoder"

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        # Fallback to configured values
        model_info["llm"]["actual"] = settings.llm_model
        model_info["ocr"]["actual"] = settings.ocr_model
        model_info["embedding"]["actual"] = settings.embedding_model
        model_info["reranker"]["actual"] = settings.rerank_model

    return model_info


def get_model_status() -> Dict[str, str]:
    """
    Get the status of each model (loaded, error, etc.)
    """
    status = {}

    try:
        # Check embedding model
        try:
            from src.utils.embedding_manager import EmbeddingManager

            embedding_manager = EmbeddingManager(settings.embedding_model)
            status["embedding"] = "✅ Loaded"
        except Exception as e:
            status["embedding"] = f"❌ Error: {str(e)[:50]}..."

        # Check OCR model (can't easily test without API call)
        status["ocr"] = "✅ Configured"

        # Check LLM model (can't easily test without API call)
        status["llm"] = "✅ Configured"

        # Check reranker model
        try:
            from sentence_transformers import CrossEncoder

            reranker = CrossEncoder(settings.rerank_model)
            status["reranker"] = "✅ Loaded"
        except Exception as e:
            status["reranker"] = f"❌ Error: {str(e)[:50]}..."

    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        status = {
            "llm": "❓ Unknown",
            "ocr": "❓ Unknown",
            "embedding": "❓ Unknown",
            "reranker": "❓ Unknown",
        }

    return status


def get_model_capabilities() -> Dict[str, Any]:
    """
    Get information about model capabilities and performance
    """
    capabilities = {
        "languages_supported": ["English", "German", "Multilingual"],
        "pdf_formats": ["PDF", "Scanned PDFs", "Multi-page documents"],
        "search_types": ["Semantic", "Exact match", "Hybrid"],
        "max_tokens": {"llm": 1000, "embedding": 512, "ocr": "Unlimited"},
        "performance": {
            "embedding_dimension": 384,
            "rerank_top_k": settings.rerank_top_k,
            "final_top_k": settings.final_top_k,
        },
    }

    # Try to get actual embedding dimension
    try:
        from src.utils.embedding_manager import EmbeddingManager

        embedding_manager = EmbeddingManager(settings.embedding_model)
        capabilities["performance"][
            "embedding_dimension"
        ] = embedding_manager.get_embedding_dimension()
    except Exception:
        pass

    return capabilities
