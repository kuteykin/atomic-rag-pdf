# tests/test_research_agent.py

"""
Tests for ResearchAgent
"""

import pytest
from src.agents.research_agent import ResearchAgent, ResearchAgentConfig
from src.schemas.query_schema import QueryType


class TestResearchAgent:
    """Test cases for ResearchAgent"""

    def test_config_creation(self):
        """Test ResearchAgentConfig creation"""
        config = ResearchAgentConfig(
            sqlite_path="./test/test.db",
            qdrant_path="./test/qdrant",
            rerank_top_k=15,
            final_top_k=7,
        )

        assert config.sqlite_path == "./test/test.db"
        assert config.qdrant_path == "./test/qdrant"
        assert config.rerank_top_k == 15
        assert config.final_top_k == 7

    def test_config_defaults(self):
        """Test ResearchAgentConfig defaults"""
        config = ResearchAgentConfig()

        assert config.sqlite_path == "./storage/products.db"
        assert config.qdrant_path == "./storage/qdrant_storage"
        assert config.rerank_top_k == 10
        assert config.final_top_k == 5
