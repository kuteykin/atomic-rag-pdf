# src/tools/translation_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import Optional, Dict, Any, List
import requests
import logging
import re
from src.config.constants import DEFAULT_LLM_MODEL

logger = logging.getLogger(__name__)


class TranslationToolConfig(BaseToolConfig):
    """Configuration for translation tool"""

    api_key: str = Field(..., description="Mistral API key")
    model: str = Field(default=DEFAULT_LLM_MODEL, description="Mistral model for translation")


class TranslationTool(BaseTool):
    """Tool for translating queries and responses using Mistral API"""

    def __init__(self, config: TranslationToolConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        try:
            # Simple language detection based on common patterns
            text_lower = text.lower()

            # German indicators
            german_patterns = [
                r"\b(der|die|das|und|oder|mit|für|von|zu|in|auf|an|bei)\b",
                r"\b(ist|sind|war|waren|wird|werden|hat|haben|hatte|hatten)\b",
                r"\b(kann|können|soll|sollen|muss|müssen|darf|dürfen)\b",
                r"\b(was|wer|wie|wo|wann|warum|welche|welcher|welches)\b",
                r"[äöüß]",  # German umlauts
            ]

            german_score = 0
            for pattern in german_patterns:
                matches = len(re.findall(pattern, text_lower))
                german_score += matches

            # English indicators
            english_patterns = [
                r"\b(the|and|or|with|for|from|to|in|on|at|by)\b",
                r"\b(is|are|was|were|will|be|has|have|had|had)\b",
                r"\b(can|could|should|must|may|might)\b",
                r"\b(what|who|how|where|when|why|which)\b",
            ]

            english_score = 0
            for pattern in english_patterns:
                matches = len(re.findall(pattern, text_lower))
                english_score += matches

            # Return detected language
            if german_score > english_score:
                return "de"
            elif english_score > 0:
                return "en"
            else:
                return "en"  # Default to English

        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return "en"  # Default to English

    def translate_to_english(self, text: str, source_lang: str = None) -> str:
        """Translate text to English"""
        if source_lang == "en" or not source_lang:
            return text

        try:
            prompt = f"""Translate the following text to English. Only return the translation, no explanations:

{text}"""

            response = self._call_mistral_api(prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"Error translating to English: {e}")
            return text  # Return original if translation fails

    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate text from English to target language"""
        if target_lang == "en":
            return text

        try:
            lang_names = {
                "de": "German",
                "fr": "French",
                "es": "Spanish",
                "it": "Italian",
                "pt": "Portuguese",
                "ru": "Russian",
                "zh": "Chinese",
                "ja": "Japanese",
                "ko": "Korean",
            }

            target_lang_name = lang_names.get(target_lang, "German")

            prompt = f"""Translate the following English text to {target_lang_name}. Only return the translation, no explanations:

{text}"""

            response = self._call_mistral_api(prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"Error translating from English: {e}")
            return text  # Return original if translation fails

    def translate_query(self, query: str) -> Dict[str, Any]:
        """Translate a query and return both original and translated versions"""
        try:
            # Detect language
            detected_lang = self.detect_language(query)

            # Translate to English if needed
            if detected_lang == "en":
                english_query = query
            else:
                english_query = self.translate_to_english(query, detected_lang)

            return {
                "original_query": query,
                "english_query": english_query,
                "detected_language": detected_lang,
                "translation_needed": detected_lang != "en",
            }

        except Exception as e:
            logger.error(f"Error translating query: {e}")
            return {
                "original_query": query,
                "english_query": query,
                "detected_language": "en",
                "translation_needed": False,
            }

    def translate_results(
        self, results: List[Dict[str, Any]], target_lang: str
    ) -> List[Dict[str, Any]]:
        """Translate search results back to target language"""
        if target_lang == "en":
            return results

        try:
            translated_results = []
            for result in results:
                translated_result = result.copy()

                # Translate text fields
                if "text" in result:
                    translated_result["text"] = self.translate_from_english(
                        result["text"], target_lang
                    )

                if "full_description" in result:
                    translated_result["full_description"] = self.translate_from_english(
                        result["full_description"], target_lang
                    )

                translated_results.append(translated_result)

            return translated_results

        except Exception as e:
            logger.error(f"Error translating results: {e}")
            return results  # Return original if translation fails

    def run(self, *args, **kwargs) -> Any:
        """Run the translation tool"""
        if len(args) > 0:
            query = args[0]
            return self.translate_query(query)
        return None

    def _call_mistral_api(self, prompt: str) -> str:
        """Call Mistral API for translation"""
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
                    "temperature": 0.1,  # Low temperature for consistent translation
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Mistral API error: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return ""
