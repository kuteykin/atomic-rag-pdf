# src/tools/parser_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from typing import List, Dict, Any
import re
import json
import logging
from src.schemas.product_schema import ProductSpecification

logger = logging.getLogger(__name__)


class StructuredParserToolConfig(BaseToolConfig):
    """Configuration for structured parser tool"""

    pass


class StructuredParserTool(BaseTool):
    """Tool for parsing structured product data from OCR text"""

    def __init__(self, config: StructuredParserToolConfig = None):
        super().__init__(config or StructuredParserToolConfig())
        self._init_patterns()

    def _init_patterns(self):
        """Initialize regex patterns for data extraction"""
        self.patterns = {
            "sku": [
                r"SKU[:\s]+([A-Z0-9\-/]+)",
                r"Artikel[:\s]+([A-Z0-9\-/]+)",
                r"Produktcode[:\s]+([A-Z0-9\-/]+)",
                r"Art\.-Nr\.?[:\s]+([A-Z0-9\-/]+)",
            ],
            "primary_product_number": [
                r"primäre\s+Erzeugnisnummer[:\s]+(\d+)",
                r"Erzeugnisnummer[:\s]+(\d+)",
                r"Produktnummer[:\s]+(\d+)",
            ],
            "watt": [
                r"(\d+)\s*W(?:att)?",
                r"(\d+)\s*W",
                r"Leistung[:\s]+(\d+)\s*W",
            ],
            "voltage": [
                r"(\d+(?:\.\d+)?)\s*V(?:olt)?",
                r"Spannung[:\s]+(\d+(?:\.\d+)?)\s*V",
            ],
            "current": [
                r"(\d+(?:\.\d+)?)\s*A(?:mpere)?",
                r"Strom[:\s]+(\d+(?:\.\d+)?)\s*A",
            ],
            "color_temperature": [
                r"(\d+)\s*K",
                r"Farbtemperatur[:\s]+(\d+)\s*K",
                r"(\d+)\s*Kelvin",
            ],
            "color_rendering_index": [
                r"CRI[:\s]+(\d+)",
                r"Farbwiedergabeindex[:\s]+(\d+)",
                r"Ra[:\s]+(\d+)",
            ],
            "luminous_flux": [
                r"(\d+)\s*Lumen",
                r"Lichtstrom[:\s]+(\d+)\s*Lumen",
                r"(\d+)\s*lm",
            ],
            "beam_angle": [
                r"(\d+(?:°|Grad))",
                r"Abstrahlwinkel[:\s]+(\d+(?:°|Grad))",
                r"Öffnungswinkel[:\s]+(\d+(?:°|Grad))",
            ],
            "lebensdauer_stunden": [
                r"(\d+)\s*Stunden",
                r"Lebensdauer[:\s]+(\d+)\s*Stunden",
                r"(\d+)\s*h",
                r"Betriebsdauer[:\s]+(\d+)\s*Stunden",
            ],
            "operating_temperature": [
                r"(\-?\d+(?:\.\d+)?)\s*°C\s*bis\s*(\-?\d+(?:\.\d+)?)\s*°C",
                r"Betriebstemperatur[:\s]+(\-?\d+(?:\.\d+)?)\s*°C\s*bis\s*(\-?\d+(?:\.\d+)?)\s*°C",
            ],
            "dimensions": [
                r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm",
                r"Abmessungen[:\s]+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm",
            ],
            "weight": [
                r"(\d+(?:\.\d+)?)\s*kg",
                r"Gewicht[:\s]+(\d+(?:\.\d+)?)\s*kg",
            ],
            "application_area": [
                r"Anwendungsbereich[:\s]+([^.\n]+)",
                r"Einsatzbereich[:\s]+([^.\n]+)",
                r"Verwendung[:\s]+([^.\n]+)",
            ],
            "ip_rating": [
                r"IP(\d+)",
                r"Schutzart[:\s]+IP(\d+)",
            ],
        }

    def run(self, text: str) -> List[ProductSpecification]:
        """Parse text and extract product specifications"""
        try:
            # Split text into potential product sections
            products = self._split_into_products(text)

            parsed_products = []
            for i, product_text in enumerate(products):
                product_data = self._extract_product_data(product_text, i)
                if product_data:
                    parsed_products.append(product_data)

            logger.info(f"Parsed {len(parsed_products)} products from text")
            return parsed_products

        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return []

    def _split_into_products(self, text: str) -> List[str]:
        """Split text into individual product sections"""
        # Look for product separators
        separators = [
            r"\n\s*[A-Z][A-Z0-9\s\-/]+\s*\n",  # Product names in caps
            r"\n\s*SKU[:\s]+",  # SKU markers
            r"\n\s*Artikel[:\s]+",  # Article markers
        ]

        # Try to split by separators
        for separator in separators:
            parts = re.split(separator, text)
            if len(parts) > 1:
                # Reconstruct with separators
                result = []
                for i, part in enumerate(parts):
                    if i > 0:
                        # Add back the separator
                        match = re.search(separator, text)
                        if match:
                            result.append(match.group() + part)
                        else:
                            result.append(part)
                    else:
                        result.append(part)
                return [p.strip() for p in result if p.strip()]

        # If no separators found, treat entire text as one product
        return [text.strip()]

    def _extract_product_data(self, text: str, index: int) -> ProductSpecification:
        """Extract product data from a text section"""
        try:
            data = {}

            # Extract basic information
            data["product_name"] = self._extract_product_name(text)
            data["sku"] = self._extract_field(text, "sku") or f"UNKNOWN_{index}"
            data["primary_product_number"] = self._extract_field(text, "primary_product_number")

            # Extract technical specifications
            data["watt"] = self._extract_numeric_field(text, "watt")
            data["voltage"] = self._extract_field(text, "voltage")
            data["current"] = self._extract_field(text, "current")

            # Extract light characteristics
            data["color_temperature"] = self._extract_field(text, "color_temperature")
            data["color_rendering_index"] = self._extract_numeric_field(
                text, "color_rendering_index"
            )
            data["luminous_flux"] = self._extract_numeric_field(text, "luminous_flux")
            data["beam_angle"] = self._extract_field(text, "beam_angle")

            # Extract lifetime and durability
            data["lebensdauer_stunden"] = self._extract_numeric_field(text, "lebensdauer_stunden")
            data["operating_temperature"] = self._extract_field(text, "operating_temperature")

            # Extract physical dimensions
            data["dimensions"] = self._extract_field(text, "dimensions")
            data["weight"] = self._extract_field(text, "weight")

            # Extract application information
            data["application_area"] = self._extract_field(text, "application_area")
            data["suitable_for"] = self._extract_suitable_for(text)

            # Extract additional specifications
            data["certifications"] = self._extract_certifications(text)
            data["ip_rating"] = self._extract_field(text, "ip_rating")

            # Set full description
            data["full_description"] = text
            data["source_pdf"] = "unknown.pdf"  # Will be set by caller

            return ProductSpecification(**data)

        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    def _extract_product_name(self, text: str) -> str:
        """Extract product name from text"""
        # Look for the first line that looks like a product name
        lines = text.split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # Check if it looks like a product name
                if re.match(r"^[A-Z][A-Z0-9\s\-/]+$", line):
                    return line
                elif re.match(r"^[A-Z][a-zA-Z0-9\s\-/]+$", line):
                    return line

        # Fallback: use first non-empty line
        for line in lines:
            line = line.strip()
            if line:
                return line[:100]  # Limit length

        return "Unknown Product"

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field using regex patterns"""
        patterns = self.patterns.get(field_name, [])

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    # Return all groups joined
                    return " ".join(match.groups())
                else:
                    return match.group(1)

        return None

    def _extract_numeric_field(self, text: str, field_name: str) -> int:
        """Extract a numeric field"""
        value = self._extract_field(text, field_name)
        if value:
            try:
                # Extract first number from the string
                numbers = re.findall(r"\d+", value)
                if numbers:
                    return int(numbers[0])
            except ValueError:
                pass
        return None

    def _extract_suitable_for(self, text: str) -> List[str]:
        """Extract suitable environments"""
        suitable_keywords = [
            "Operationssaal",
            "OP",
            "Krankenhaus",
            "Klinik",
            "Büro",
            "Office",
            "Wohnung",
            "Wohnraum",
            "Industrie",
            "Industriell",
            "Fabrik",
            "Außenbereich",
            "Außen",
            "Outdoor",
            "Feuchtraum",
            "Bad",
            "Küche",
            "Lager",
            "Werkstatt",
            "Garage",
        ]

        found = []
        text_lower = text.lower()

        for keyword in suitable_keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)

        return found

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        cert_patterns = [
            r"CE",
            r"EN\s*\d+",
            r"IEC\s*\d+",
            r"UL",
            r"FCC",
            r"RoHS",
            r"IP\d+",
        ]

        found = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)

        return list(set(found))  # Remove duplicates
