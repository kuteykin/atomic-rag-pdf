# tests/test_qa_agent.py

"""
Tests for QualityAssuranceAgent
"""

import pytest
from src.agents.qa_agent import QualityAssuranceAgent, QAAgentConfig


class TestQualityAssuranceAgent:
    """Test cases for QualityAssuranceAgent"""

    def test_config_creation(self):
        """Test QAAgentConfig creation"""
        config = QAAgentConfig(llm_model="test-model", language="English", max_answer_length=1000)

        assert config.llm_model == "test-model"
        assert config.language == "English"
        assert config.max_answer_length == 1000

    def test_config_defaults(self):
        """Test QAAgentConfig defaults"""
        config = QAAgentConfig()

        assert config.llm_model == "mistral-large-latest"
        assert config.language == "German"
        assert config.max_answer_length == 500
