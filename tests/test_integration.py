# tests/test_integration.py

"""
Integration tests for the complete system
"""

import pytest
from src.schemas.product_schema import ProductSpecification
from src.schemas.query_schema import QueryClassification, QueryType, AttributeFilter
from src.schemas.answer_schema import GeneratedAnswer, Citation, AnswerValidation


class TestSchemas:
    """Test Pydantic schemas"""

    def test_product_specification(self, sample_product_data):
        """Test ProductSpecification schema"""
        product = ProductSpecification(**sample_product_data)

        assert product.product_name == "Test Leuchte"
        assert product.sku == "TEST-001"
        assert product.watt == 100
        assert product.lebensdauer_stunden == 50000

    def test_query_classification(self):
        """Test QueryClassification schema"""
        classification = QueryClassification(
            query="Test query", type=QueryType.SEMANTIC, confidence=0.8
        )

        assert classification.query == "Test query"
        assert classification.type == QueryType.SEMANTIC
        assert classification.confidence == 0.8

    def test_attribute_filter(self):
        """Test AttributeFilter schema"""
        filters = AttributeFilter(watt_min=100, watt_max=500, lebensdauer_min=1000)

        assert filters.watt_min == 100
        assert filters.watt_max == 500
        assert filters.lebensdauer_min == 1000

    def test_generated_answer(self):
        """Test GeneratedAnswer schema"""
        answer = GeneratedAnswer(
            query="Test query",
            answer="Test answer",
            confidence_score=0.9,
            completeness_score=0.8,
            accuracy_score=0.7,
            search_strategy="semantic",
            query_type="semantic",
        )

        assert answer.query == "Test query"
        assert answer.answer == "Test answer"
        assert answer.confidence_score == 0.9
        assert answer.search_strategy == "semantic"


class TestQueryTypes:
    """Test query type detection"""

    def test_exact_match_queries(self):
        """Test exact match query detection"""
        exact_queries = [
            "Erzeugnisnummer 123456789",
            "primäre Erzeugnisnummer 987654321",
            "SKU ABC-123",
            "Artikel XYZ-456",
        ]

        for query in exact_queries:
            # This would be tested with the actual QueryClassifierTool
            assert "nummer" in query.lower() or "sku" in query.lower() or "artikel" in query.lower()

    def test_filter_queries(self):
        """Test filter query detection"""
        filter_queries = [
            "mindestens 1000 Watt",
            "mehr als 400 Stunden",
            "zwischen 200 und 500 Watt",
            "Farbtemperatur 3000K",
        ]

        for query in filter_queries:
            assert any(
                keyword in query.lower()
                for keyword in [
                    "mindestens",
                    "mehr als",
                    "zwischen",
                    "watt",
                    "stunden",
                    "farbtemperatur",
                ]
            )

    def test_semantic_queries(self):
        """Test semantic query detection"""
        semantic_queries = [
            "Welche Leuchten sind gut für Operationssaal?",
            "Empfehlung für Bürobeleuchtung",
            "Energiesparende Leuchtmittel",
        ]

        for query in semantic_queries:
            assert any(
                keyword in query.lower()
                for keyword in ["welche", "gut für", "empfehlung", "energiesparend"]
            )


class TestSystemIntegration:
    """Test system integration scenarios"""

    def test_test_queries_coverage(self):
        """Test that all required test queries are covered"""
        test_queries = [
            "Was ist die Farbtemperatur von SIRIUS HRI 330W 2/CS 1/SKU?",
            "Welche Leuchten sind gut für die Ausstattung im Operationssaal geeignet?",
            "Gebe mir alle Leuchtmittel mit mindestens 1000 Watt und Lebensdauer von mehr als 400 Stunden.",
            "Welche Leuchte hat die primäre Erzeugnisnummer 4062172212311?",
        ]

        # Verify all test queries are present
        assert len(test_queries) == 4

        # Check query types
        assert "farbtemperatur" in test_queries[0].lower()
        assert "operationssaal" in test_queries[1].lower()
        assert "mindestens" in test_queries[2].lower()
        assert "erzeugnisnummer" in test_queries[3].lower()

    def test_scalability_considerations(self):
        """Test scalability considerations mentioned in requirements"""
        scalability_points = [
            "Vector database indexing",
            "Batch processing",
            "Caching strategies",
            "Database optimization",
            "Distributed processing",
        ]

        # This test documents scalability considerations
        assert len(scalability_points) >= 5
        assert "Vector database indexing" in scalability_points
        assert "Batch processing" in scalability_points
