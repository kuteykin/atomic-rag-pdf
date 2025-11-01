# src/tools/answer_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List, Dict, Any, Optional
import requests
import json
import logging
from src.schemas.answer_schema import GeneratedAnswer, Citation, AnswerValidation
from src.config.settings import settings
from src.config.constants import DEFAULT_LLM_MODEL

logger = logging.getLogger(__name__)


class AnswerGeneratorToolConfig(BaseToolConfig):
    """Configuration for answer generator tool"""

    model: str = Field(default=DEFAULT_LLM_MODEL)
    api_key: str = Field(..., description="Mistral API key")


class AnswerGeneratorTool(BaseTool):
    """Tool for generating answers using LLM"""

    def __init__(self, config: AnswerGeneratorToolConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model

    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate answer from query and context"""
        try:
            # Prepare context text
            context_text = self._prepare_context(context)

            # Create prompt
            prompt = self._create_prompt(query, context_text)

            # Call Mistral API
            response = self._call_mistral_api(prompt)

            return response

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Entschuldigung, ich konnte keine Antwort generieren. Fehler: {str(e)}"

    def _prepare_context(self, context: List[Dict[str, Any]]) -> str:
        """Prepare context text from search results"""
        context_parts = []

        for i, result in enumerate(context, 1):
            product_name = result.get("product_name", "Unbekanntes Produkt")
            sku = result.get("sku", "N/A")
            text = result.get("text", result.get("full_description", ""))

            context_part = f"""
Produkt {i}: {product_name}
SKU: {sku}
Beschreibung: {text}
"""
            context_parts.append(context_part)

        return "\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for LLM"""
        prompt = f"""Du bist ein Experte für Beleuchtungsprodukte. Beantworte die folgende Frage basierend auf den bereitgestellten Produktinformationen.

Frage: {query}

Produktinformationen:
{context}

Anweisungen:
1. Beantworte die Frage präzise und vollständig auf Deutsch
2. Verwende nur die bereitgestellten Informationen
3. Wenn die Information nicht verfügbar ist, sage das explizit
4. Erwähne relevante Produktnamen und SKUs
5. Sei hilfreich und professionell

Antwort:"""

        return prompt

    def _call_mistral_api(self, prompt: str) -> str:
        """Call Mistral API"""
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.3,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Mistral API error: {response.status_code} - {response.text}")
                return "Fehler beim Generieren der Antwort."

        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return "Fehler beim Generieren der Antwort."

    def run(self, query: str, context: list = None, **kwargs) -> dict:
        """Required by BaseTool - generates answers"""
        if context:
            answer = self.generate(query, context)
            return {"answer": answer}
        else:
            return {"answer": "No context provided for answer generation"}


class FactCheckerToolConfig(BaseToolConfig):
    """Configuration for fact checker tool"""

    pass


class FactCheckerTool(BaseTool):
    """Tool for fact-checking answers against sources"""

    def __init__(self, config: FactCheckerToolConfig = None):
        super().__init__(config or FactCheckerToolConfig())

    def verify(self, answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify facts in answer against sources"""
        try:
            # Extract claims from answer
            claims = self._extract_claims(answer)

            # Verify each claim
            verification_results = []
            for claim in claims:
                verification = self._verify_claim(claim, sources)
                verification_results.append(verification)

            # Calculate overall verification score
            verified_count = sum(1 for v in verification_results if v["verified"])
            total_count = len(verification_results)
            verification_score = verified_count / total_count if total_count > 0 else 0

            return {
                "verified_facts": verified_count,
                "unverified_facts": total_count - verified_count,
                "verification_score": verification_score,
                "claim_verifications": verification_results,
            }

        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return {
                "verified_facts": 0,
                "unverified_facts": 0,
                "verification_score": 0,
                "claim_verifications": [],
            }

    def _extract_claims(self, answer: str) -> List[str]:
        """Extract factual claims from answer"""
        # Simple claim extraction - look for statements with numbers or specific facts
        import re

        # Split into sentences
        sentences = re.split(r"[.!?]+", answer)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Only consider substantial sentences
                # Look for sentences with numbers or specific facts
                if re.search(r"\d+", sentence) or any(
                    keyword in sentence.lower()
                    for keyword in [
                        "watt",
                        "stunden",
                        "kelvin",
                        "lumen",
                        "volt",
                        "ampere",
                        "ip",
                        "cri",
                    ]
                ):
                    claims.append(sentence)

        return claims

    def _verify_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a single claim against sources"""
        claim_lower = claim.lower()

        # Check if claim appears in any source
        for source in sources:
            source_text = (
                source.get("text", "") + " " + source.get("full_description", "")
            ).lower()

            # Simple keyword matching
            claim_words = set(claim_lower.split())
            source_words = set(source_text.split())

            # Calculate overlap
            overlap = len(claim_words.intersection(source_words))
            total_words = len(claim_words)

            if total_words > 0 and overlap / total_words > 0.3:  # 30% word overlap
                return {
                    "claim": claim,
                    "verified": True,
                    "source": source.get("product_name", "Unknown"),
                    "confidence": overlap / total_words,
                }

        return {"claim": claim, "verified": False, "source": None, "confidence": 0.0}

    def run(self, answer: str = "", sources: list = None, **kwargs) -> dict:
        """Required by BaseTool - verifies facts"""
        if answer and sources:
            return self.verify(answer, sources)
        else:
            return {"verified": False, "message": "No answer or sources provided"}


class CitationToolConfig(BaseToolConfig):
    """Configuration for citation tool"""

    pass


class CitationTool(BaseTool):
    """Tool for adding citations to answers"""

    def __init__(self, config: CitationToolConfig = None):
        super().__init__(config or CitationToolConfig())

    def add_citations(
        self, answer: str, sources: List[Dict[str, Any]], fact_check: Dict[str, Any]
    ) -> str:
        """Add citations to answer"""
        try:
            # Create citations for verified facts
            citations = []
            for verification in fact_check.get("claim_verifications", []):
                if verification["verified"]:
                    citation = Citation(
                        claim=verification["claim"],
                        source=verification["source"],
                        pdf_source=(
                            sources[0].get("source_pdf", "Unknown PDF")
                            if sources
                            else "Unknown PDF"
                        ),
                        confidence=verification["confidence"],
                    )
                    citations.append(citation)

            # Add source references at the end
            if sources:
                answer += "\n\n**Quellen:**\n"
                for i, source in enumerate(sources, 1):
                    product_name = source.get("product_name", "Unbekanntes Produkt")
                    sku = source.get("sku", "N/A")
                    pdf_source = source.get("source_pdf", "Unbekannte PDF")

                    answer += f"{i}. {product_name} (SKU: {sku}) - {pdf_source}\n"

            return answer

        except Exception as e:
            logger.error(f"Error adding citations: {e}")
            return answer

    def run(self, answer: str = "", sources: list = None, **kwargs) -> dict:
        """Required by BaseTool - adds citations"""
        if answer and sources:
            cited_answer = self.add_citations(answer, sources)
            return {"cited_answer": cited_answer}
        else:
            return {"cited_answer": answer, "message": "No sources provided"}


class ValidationToolConfig(BaseToolConfig):
    """Configuration for validation tool"""

    pass


class ValidationTool(BaseTool):
    """Tool for validating answer completeness and accuracy"""

    def __init__(self, config: ValidationToolConfig = None):
        super().__init__(config or ValidationToolConfig())

    def validate(self, query: str, answer: str, sources: List[Dict[str, Any]]) -> AnswerValidation:
        """Validate answer completeness and accuracy"""
        try:
            # Check completeness
            completeness_score = self._check_completeness(query, answer)

            # Check accuracy
            accuracy_score = self._check_accuracy(answer, sources)

            # Calculate overall confidence
            confidence_score = (completeness_score + accuracy_score) / 2

            # Generate warnings
            warnings = self._generate_warnings(query, answer, sources)

            return AnswerValidation(
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                confidence_score=confidence_score,
                warnings=warnings,
                verified_facts=0,  # Will be filled by fact checker
                unverified_facts=0,  # Will be filled by fact checker
                sources_used=len(sources),
                source_coverage=min(len(sources) / 5, 1.0),  # Assume 5 sources is full coverage
            )

        except Exception as e:
            logger.error(f"Error in validation: {e}")
            return AnswerValidation(
                completeness_score=0.0,
                accuracy_score=0.0,
                confidence_score=0.0,
                warnings=[f"Validation error: {str(e)}"],
                verified_facts=0,
                unverified_facts=0,
                sources_used=len(sources),
                source_coverage=0.0,
            )

    def _check_completeness(self, query: str, answer: str) -> float:
        """Check if answer is complete"""
        query_lower = query.lower()
        answer_lower = answer.lower()

        # Check for common completeness indicators
        completeness_indicators = [
            "entschuldigung" in answer_lower,  # Apology suggests incomplete
            "nicht verfügbar" in answer_lower,  # Not available
            "keine information" in answer_lower,  # No information
            len(answer) < 50,  # Very short answer
        ]

        if any(completeness_indicators):
            return 0.3

        # Check if answer addresses the query
        query_words = set(query_lower.split())
        answer_words = set(answer_lower.split())

        # Calculate word overlap
        overlap = len(query_words.intersection(answer_words))
        total_query_words = len(query_words)

        if total_query_words > 0:
            overlap_score = overlap / total_query_words
            return min(overlap_score + 0.5, 1.0)  # Boost by 0.5

        return 0.5

    def _check_accuracy(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """Check answer accuracy"""
        if not sources:
            return 0.0

        # Simple accuracy check based on source coverage
        answer_lower = answer.lower()

        # Count how many sources are referenced
        referenced_sources = 0
        for source in sources:
            product_name = source.get("product_name", "").lower()
            sku = source.get("sku", "").lower()

            if product_name in answer_lower or sku in answer_lower:
                referenced_sources += 1

        # Calculate accuracy based on source referencing
        accuracy_score = referenced_sources / len(sources)

        return accuracy_score

    def _generate_warnings(
        self, query: str, answer: str, sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate warnings about the answer"""
        warnings = []

        if len(sources) == 0:
            warnings.append("Keine Quellen gefunden")

        if len(sources) < 2:
            warnings.append("Wenige Quellen verfügbar")

        if len(answer) < 100:
            warnings.append("Antwort ist sehr kurz")

        if "entschuldigung" in answer.lower():
            warnings.append("Unvollständige Informationen verfügbar")

        return warnings

    def run(self, query: str = "", answer: str = "", sources: list = None, **kwargs) -> dict:
        """Required by BaseTool - validates answers"""
        if query and answer and sources:
            validation = self.validate(query, answer, sources)
            return validation.dict()
        else:
            return {
                "confidence": 0.0,
                "completeness": 0.0,
                "accuracy": 0.0,
                "warnings": ["Insufficient data for validation"],
            }
