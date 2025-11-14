# src/config/constants.py

"""
Application constants and default configuration values.
These values are used as defaults throughout the application.
Override via environment variables for environment-specific settings (API keys, paths).
"""

# =============================================================================
# MODEL CONSTANTS
# =============================================================================

# LLM Models
DEFAULT_LLM_MODEL: str = "mistral-large-latest"
DEFAULT_OCR_MODEL: str = "mistral-ocr-latest"

# Embedding Models
DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# Reranking Models
DEFAULT_RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# =============================================================================
# PATH CONSTANTS
# =============================================================================

# Storage paths
DEFAULT_SQLITE_PATH: str = "./storage/products.db"
DEFAULT_QDRANT_PATH: str = "./storage/qdrant_storage"
DEFAULT_PDF_DIRECTORY: str = "./data/pdfs"

# Collection names
DEFAULT_COLLECTION_NAME: str = "products"

# =============================================================================
# SEARCH CONFIGURATION
# =============================================================================

# Result limits
DEFAULT_RERANK_TOP_K: int = 10
DEFAULT_FINAL_TOP_K: int = 5
DEFAULT_INITIAL_CANDIDATES: int = 20

# Search strategy weights
DEFAULT_SEMANTIC_WEIGHT: float = 0.7
DEFAULT_EXACT_WEIGHT: float = 0.3

# Reranking
DEFAULT_ENABLE_RERANKING: bool = True

# =============================================================================
# TEXT PROCESSING
# =============================================================================

# Chunking
DEFAULT_CHUNK_SIZE: int = 500
DEFAULT_CHUNK_OVERLAP: int = 30

# =============================================================================
# LANGUAGE SETTINGS
# =============================================================================

DEFAULT_LANGUAGE: str = "en"
DEFAULT_QA_LANGUAGE: str = "German"

# =============================================================================
# ANSWER GENERATION
# =============================================================================

DEFAULT_MAX_ANSWER_LENGTH: int = 500

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# Temperature settings
DEFAULT_CLASSIFIER_TEMPERATURE: float = 0.1

# =============================================================================
# LOGGING
# =============================================================================

DEFAULT_LOG_LEVEL: str = "INFO"
