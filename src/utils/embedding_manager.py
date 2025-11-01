# src/utils/embedding_manager.py

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import os
from src.config.constants import DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding generation with CPU-only German models"""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        # Force CPU usage
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

        try:
            self.model = SentenceTransformer(model_name, device="cpu")
            logger.info(f"Loaded embedding model: {model_name} on CPU")
        except Exception as e:
            logger.warning(f"Failed to load {model_name}, falling back to basic model: {e}")
            # Fallback to basic English model
            self.model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL, device="cpu")
            logger.info(f"Loaded fallback English model: {DEFAULT_EMBEDDING_MODEL} on CPU")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False, device="cpu")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384  # Default dimension for MiniLM models

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False, device="cpu")
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 384 for _ in texts]

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
