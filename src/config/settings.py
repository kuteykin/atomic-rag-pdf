# src/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional
from .constants import (
    DEFAULT_SQLITE_PATH,
    DEFAULT_QDRANT_PATH,
    DEFAULT_PDF_DIRECTORY,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_OCR_MODEL,
    DEFAULT_RERANK_MODEL,
    DEFAULT_RERANK_TOP_K,
    DEFAULT_FINAL_TOP_K,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_LANGUAGE,
    DEFAULT_LOG_LEVEL,
)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Only API keys and environment-specific overrides should be in .env file.
    All default values come from constants.py.
    """

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # API Keys (required from .env or environment)
    mistral_api_key: str = Field(..., description="Mistral API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (optional)")

    # Database paths (optional overrides)
    sqlite_path: str = Field(
        default=DEFAULT_SQLITE_PATH, description="SQLite database path"
    )
    qdrant_path: str = Field(
        default=DEFAULT_QDRANT_PATH, description="Qdrant storage path"
    )

    # PDF processing (optional override)
    pdf_directory: str = Field(
        default=DEFAULT_PDF_DIRECTORY, description="PDF input directory"
    )

    # LLM configuration (optional overrides)
    llm_model: str = Field(default=DEFAULT_LLM_MODEL, description="LLM model name")
    embedding_model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        description="English-optimized embedding model",
    )

    # Search configuration (optional overrides)
    rerank_top_k: int = Field(
        default=DEFAULT_RERANK_TOP_K, description="Number of results to rerank"
    )
    final_top_k: int = Field(
        default=DEFAULT_FINAL_TOP_K, description="Final number of results"
    )

    # OCR configuration (optional override)
    ocr_model: str = Field(
        default=DEFAULT_OCR_MODEL, description="Mistral OCR model - optimal for English PDFs"
    )

    # Reranking configuration (optional override)
    rerank_model: str = Field(
        default=DEFAULT_RERANK_MODEL, description="Reranking model"
    )

    # Text processing (optional overrides)
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, description="Text chunk size")
    chunk_overlap: int = Field(
        default=DEFAULT_CHUNK_OVERLAP, description="Text chunk overlap"
    )

    # Language settings (optional override)
    default_language: str = Field(
        default=DEFAULT_LANGUAGE, description="Default language"
    )

    # Logging (optional override)
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, description="Logging level")


# Global settings instance
settings = Settings()
