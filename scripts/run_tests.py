# scripts/run_tests.py

"""
Run test queries for the Atomic RAG System
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.research_agent import ResearchAgent, ResearchAgentConfig
from src.agents.qa_agent import QualityAssuranceAgent, QAAgentConfig
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run test queries"""
    print("🧪 Running test queries...")

    # Test queries from the requirements
    test_queries = [
        "Was ist die Farbtemperatur von SIRIUS HRI 330W 2/CS 1/SKU?",
        "Welche Leuchten sind gut für die Ausstattung im Operationssaal geeignet?",
        "Gebe mir alle Leuchtmittel mit mindestens 1000 Watt und Lebensdauer von mehr als 400 Stunden.",
        "Welche Leuchte hat die primäre Erzeugnisnummer 4062172212311?",
    ]

    try:
        # Initialize agents
        research_agent = ResearchAgent(ResearchAgentConfig())
        qa_agent = QualityAssuranceAgent(QAAgentConfig())

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/4: {query}")
            print("=" * 60)

            # Search
            search_results = research_agent.search(query)
            print(f"Found {search_results['total_results']} results")

            # Generate answer
            answer = qa_agent.generate_answer(query, search_results)

            print(f"\nAnswer: {answer['answer']}")
            print(f"Confidence: {answer['confidence_score']:.2%}")
            print(f"Sources: {answer['sources_used']}")

    except Exception as e:
        logger.error(f"Error running tests: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
