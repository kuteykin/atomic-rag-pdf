# src/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # API Keys
    mistral_api_key: str = Field(..., description="Mistral API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (optional)")

    # Database paths
    sqlite_path: str = Field(default="./storage/products.db", description="SQLite database path")
    qdrant_path: str = Field(default="./storage/qdrant_storage", description="Qdrant storage path")

    # PDF processing
    pdf_directory: str = Field(default="./data/pdfs", description="PDF input directory")

    # LLM configuration
    llm_model: str = Field(default="mistral-large-latest", description="LLM model name")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="English-optimized embedding model",
    )

    # Search configuration
    rerank_top_k: int = Field(default=10, description="Number of results to rerank")
    final_top_k: int = Field(default=5, description="Final number of results")

    # OCR configuration
    ocr_model: str = Field(
        default="mistral-ocr-latest", description="Mistral OCR model - optimal for English PDFs"
    )

    # Reranking configuration
    rerank_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", description="Reranking model"
    )

    # Text processing
    chunk_size: int = Field(default=500, description="Text chunk size")
    chunk_overlap: int = Field(default=50, description="Text chunk overlap")

    # Language settings
    default_language: str = Field(default="en", description="Default language")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
