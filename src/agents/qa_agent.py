# src/agents/qa_agent.py

from src.lib.base_agent import BaseAgent, BaseAgentConfig
from pydantic import Field


class QAAgentConfig(BaseAgentConfig):
    """Configuration for QA Agent"""

    llm_model: str = Field(default="mistral-large-latest")
    language: str = Field(default="German")
    max_answer_length: int = Field(default=500)


class QualityAssuranceAgent(BaseAgent):
    """
    Agent responsible for:
    1. Generating natural language answers from retrieved data
    2. Fact-checking against source materials
    3. Adding proper citations
    4. Validating answer completeness and accuracy
    """

    def __init__(self, config: QAAgentConfig):
        from src.tools.answer_tools import (
            AnswerGeneratorTool,
            AnswerGeneratorToolConfig,
            FactCheckerTool,
            FactCheckerToolConfig,
            CitationTool,
            CitationToolConfig,
            ValidationTool,
            ValidationToolConfig,
        )
        from src.tools.translation_tools import TranslationTool, TranslationToolConfig
        from src.config.settings import settings

        # Initialize tools
        self.generator_tool = AnswerGeneratorTool(
            AnswerGeneratorToolConfig(model=config.llm_model, api_key=settings.mistral_api_key)
        )
        self.fact_checker_tool = FactCheckerTool(FactCheckerToolConfig())
        self.citation_tool = CitationTool(CitationToolConfig())
        self.validation_tool = ValidationTool(ValidationToolConfig())
        self.translation_tool = TranslationTool(
            TranslationToolConfig(api_key=settings.mistral_api_key)
        )

        # Initialize base agent
        super().__init__(config)

    def generate_answer(self, query: str, search_results: dict) -> dict:
        """Generate and validate answer with translation support"""

        # Detect if query needs translation
        detected_language = search_results.get("detected_language", "en")
        translation_needed = search_results.get("translation_needed", False)

        # Use English query for answer generation
        english_query = search_results.get("english_query", query)

        # Step 1: Generate initial answer in English
        draft_answer = self.generator_tool.generate(
            query=english_query, context=search_results["top_results"]
        )

        # Step 2: Fact-check
        fact_check_result = self.fact_checker_tool.verify(
            answer=draft_answer, sources=search_results["top_results"]
        )

        # Step 3: Add citations
        cited_answer = self.citation_tool.add_citations(
            answer=draft_answer,
            sources=search_results["top_results"],
            fact_check=fact_check_result,
        )

        # Step 4: Translate answer back to original language if needed
        final_answer = cited_answer
        if translation_needed and detected_language != "en":
            final_answer = self.translation_tool.translate_from_english(
                cited_answer, detected_language
            )

        # Step 5: Validate completeness and accuracy
        validation_result = self.validation_tool.validate(
            query=english_query, answer=final_answer, sources=search_results["top_results"]
        )

        return {
            "query": query,
            "english_query": english_query,
            "detected_language": detected_language,
            "translation_needed": translation_needed,
            "answer": final_answer,
            "confidence_score": validation_result.confidence_score,
            "completeness_score": validation_result.completeness_score,
            "accuracy_score": validation_result.accuracy_score,
            "sources_used": len(search_results["top_results"]),
            "warnings": validation_result.warnings or [],
            "metadata": {
                "query_type": search_results["query_type"],
                "search_strategy": search_results["search_strategy"],
                "total_results_found": search_results["total_results"],
            },
        }

    def process(self, query: str, search_results: dict, **kwargs) -> dict:
        """Required by BaseAgent - processes QA queries"""
        return self.generate_answer(query, search_results)
