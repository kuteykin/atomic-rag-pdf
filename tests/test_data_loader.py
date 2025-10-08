# tests/test_data_loader.py

"""
Tests for DataLoaderAgent
"""

import pytest
from src.agents.data_loader_agent import DataLoaderAgent, DataLoaderAgentConfig
from src.schemas.product_schema import ProductSpecification


class TestDataLoaderAgent:
    """Test cases for DataLoaderAgent"""

    def test_chunk_text(self):
        """Test text chunking functionality"""
        text = "This is a test text with multiple words that should be chunked properly for processing."

        chunks = DataLoaderAgent.chunk_text(text, chunk_size=10, overlap=2)

        assert len(chunks) > 0
        assert all(len(chunk.split()) <= 10 for chunk in chunks)
        assert chunks[0].startswith("This is a")

    def test_chunk_text_empty(self):
        """Test chunking empty text"""
        chunks = DataLoaderAgent.chunk_text("")
        assert chunks == []

    def test_chunk_text_short(self):
        """Test chunking short text"""
        text = "Short text"
        chunks = DataLoaderAgent.chunk_text(text, chunk_size=20)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_config_creation(self):
        """Test DataLoaderAgentConfig creation"""
        config = DataLoaderAgentConfig(
            pdf_directory="./test/pdfs", sqlite_path="./test/test.db", qdrant_path="./test/qdrant"
        )

        assert config.pdf_directory == "./test/pdfs"
        assert config.sqlite_path == "./test/test.db"
        assert config.qdrant_path == "./test/qdrant"

    def test_config_defaults(self):
        """Test DataLoaderAgentConfig defaults"""
        config = DataLoaderAgentConfig()

        assert config.pdf_directory == "./data/pdfs"
        assert config.sqlite_path == "./storage/products.db"
        assert config.qdrant_path == "./storage/qdrant_storage"
