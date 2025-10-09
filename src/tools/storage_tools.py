# src/tools/storage_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List, Dict, Any, Optional
import sqlite3
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import logging
from src.utils.db_manager import DatabaseManager
from src.utils.embedding_manager import EmbeddingManager
from src.schemas.product_schema import ProductSpecification

logger = logging.getLogger(__name__)


class SQLiteStorageToolConfig(BaseToolConfig):
    """Configuration for SQLite storage tool"""

    db_path: str = Field(default="./storage/products.db")


class SQLiteStorageTool(BaseTool):
    """Tool for storing structured data in SQLite"""

    def __init__(self, config: SQLiteStorageToolConfig):
        super().__init__(config)
        self.db_manager = DatabaseManager(config.db_path)

    def insert_product(self, product: ProductSpecification) -> int:
        """Insert a product and return the ID"""
        try:
            product_dict = product.dict()
            product_id = self.db_manager.insert_product(product_dict)
            logger.info(f"Inserted product {product.sku} with ID {product_id}")
            return product_id
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            raise

    def upsert_product(self, product: ProductSpecification) -> int:
        """Insert or update a product and return the ID"""
        try:
            product_dict = product.dict()
            product_id = self.db_manager.upsert_product(product_dict)
            logger.info(f"Upserted product {product.sku} with ID {product_id}")
            return product_id
        except Exception as e:
            logger.error(f"Error upserting product: {e}")
            raise

    def search_exact(self, query: str) -> List[Dict[str, Any]]:
        """Search for exact matches"""
        return self.db_manager.search_exact(query)

    def search_by_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search by attribute filters"""
        return self.db_manager.search_by_filters(filters)

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        return self.db_manager.get_product_by_id(product_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db_manager.get_stats()

    def run(self, **kwargs) -> Dict[str, Any]:
        """Required by BaseTool - returns database stats"""
        return self.get_stats()


class QdrantStorageToolConfig(BaseToolConfig):
    """Configuration for Qdrant storage tool"""

    qdrant_path: str = Field(default="./storage/qdrant_storage")
    collection_name: str = Field(default="products")


class QdrantStorageTool(BaseTool):
    """Tool for storing embeddings in Qdrant"""

    _instances = {}  # Class variable to store instances

    def __new__(cls, config: QdrantStorageToolConfig):
        # Create a unique key for this configuration
        key = f"{config.qdrant_path}:{config.collection_name}"

        # Return existing instance if it exists
        if key in cls._instances:
            return cls._instances[key]

        # Create new instance
        instance = super().__new__(cls)
        cls._instances[key] = instance
        return instance

    def __init__(self, config: QdrantStorageToolConfig):
        # Only initialize if not already initialized
        if not hasattr(self, "_initialized"):
            super().__init__(config)
            self.client = QdrantClient(path=config.qdrant_path)
            self.collection_name = config.collection_name
            self._init_collection()
            self._initialized = True

    def _init_collection(self):
        """Initialize Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE,  # Dimension for multilingual MiniLM models
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise

    def insert_point(self, vector: List[float], payload: Dict[str, Any]) -> str:
        """Insert a point with vector and payload"""
        try:
            point_id = str(uuid.uuid4())

            point = PointStruct(id=point_id, vector=vector, payload=payload)

            self.client.upsert(collection_name=self.collection_name, points=[point])

            logger.debug(f"Inserted point {point_id} into Qdrant")
            return point_id

        except Exception as e:
            logger.error(f"Error inserting point into Qdrant: {e}")
            raise

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter_conditions,
            )

            results = []
            for point in search_result:
                result = {"id": point.id, "score": point.score, "payload": point.payload}
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

    def delete_points(self, point_ids: List[str]):
        """Delete points by IDs"""
        try:
            self.client.delete(collection_name=self.collection_name, points_selector=point_ids)
            logger.info(f"Deleted {len(point_ids)} points from Qdrant")
        except Exception as e:
            logger.error(f"Error deleting points from Qdrant: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def run(self, **kwargs) -> Dict[str, Any]:
        """Required by BaseTool - returns collection info"""
        return self.get_collection_info()


class EmbeddingToolConfig(BaseToolConfig):
    """Configuration for embedding tool"""

    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")


class EmbeddingTool(BaseTool):
    """Tool for generating text embeddings"""

    def __init__(self, config: EmbeddingToolConfig = None):
        super().__init__(config or EmbeddingToolConfig())
        self.embedding_manager = EmbeddingManager(self.config.model_name)

    def generate(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_manager.generate_embedding(text)

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return self.embedding_manager.generate_embeddings_batch(texts)

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_manager.get_embedding_dimension()

    def run(self, text: str = "", **kwargs) -> Dict[str, Any]:
        """Required by BaseTool - generates embedding for text"""
        if text:
            embedding = self.generate(text)
            return {"embedding": embedding, "dimension": len(embedding)}
        else:
            return {"dimension": self.get_dimension()}
