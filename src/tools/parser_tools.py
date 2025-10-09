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
                # English patterns (prioritized)
                r"SKU[:\s]+([A-Z0-9\-/]+)",
                r"Product[:\s]+Code[:\s]+([A-Z0-9\-/]+)",
                r"Item[:\s]+Number[:\s]+([A-Z0-9\-/]+)",
                r"Part[:\s]+Number[:\s]+([A-Z0-9\-/]+)",
                r"Model[:\s]+Number[:\s]+([A-Z0-9\-/]+)",
                r"Product[:\s]+ID[:\s]+([A-Z0-9\-/]+)",
                r"Code[:\s]+([A-Z0-9\-/]+)",
                r"ZMP[_\s]*(\d+)",  # ZMP product codes
                r"^#\s*(\d+)\s*W",  # Product codes at start of line
                # German patterns (fallback)
                r"Artikel[:\s]+([A-Z0-9\-/]+)",
                r"Produktcode[:\s]+([A-Z0-9\-/]+)",
                r"Art\.-Nr\.?[:\s]+([A-Z0-9\-/]+)",
            ],
            "primary_product_number": [
                # English patterns (prioritized)
                r"Primary[:\s]+Product[:\s]+Number[:\s]+(\d+)",
                r"Product[:\s]+Number[:\s]+(\d+)",
                r"Main[:\s]+Number[:\s]+(\d+)",
                # German patterns (fallback)
                r"primäre\s+Erzeugnisnummer[:\s]+(\d+)",
                r"Erzeugnisnummer[:\s]+(\d+)",
                r"Produktnummer[:\s]+(\d+)",
            ],
            "watt": [
                # English patterns (prioritized)
                r"(\d{1,4})\s*W(?:att)?\b",
                r"Power[:\s]+(\d{1,4})\s*W",
                r"Wattage[:\s]+(\d{1,4})\s*W",
                r"(\d{1,4})\s*W\b",
                # German patterns (fallback)
                r"Leistung[:\s]+(\d{1,4})\s*W",
            ],
            "voltage": [
                # English patterns (prioritized)
                r"(\d+(?:\.\d+)?)\s*V(?:olt)?\b",
                r"Voltage[:\s]+(\d+(?:\.\d+)?)\s*V",
                r"Operating[:\s]+Voltage[:\s]+(\d+(?:\.\d+)?)\s*V",
                # German patterns (fallback)
                r"Spannung[:\s]+(\d+(?:\.\d+)?)\s*V",
            ],
            "current": [
                # English patterns (prioritized)
                r"(\d+(?:\.\d+)?)\s*A(?:mpere)?\b",
                r"Current[:\s]+(\d+(?:\.\d+)?)\s*A",
                r"Amperage[:\s]+(\d+(?:\.\d+)?)\s*A",
                # German patterns (fallback)
                r"Strom[:\s]+(\d+(?:\.\d+)?)\s*A",
            ],
            "color_temperature": [
                # English patterns (prioritized)
                r"(\d+)\s*K(?:elvin)?\b",
                r"Color[:\s]+Temperature[:\s]+(\d+)\s*K",
                r"Temperature[:\s]+(\d+)\s*K",
                r"CCT[:\s]+(\d+)\s*K",
                # German patterns (fallback)
                r"Farbtemperatur[:\s]+(\d+)\s*K",
                r"(\d+)\s*Kelvin",
            ],
            "color_rendering_index": [
                r"CRI[:\s]+(\d+)",
                r"Farbwiedergabeindex[:\s]+(\d+)",
                r"Ra[:\s]+(\d+)",
            ],
            "luminous_flux": [
                # English patterns (prioritized)
                r"(\d+)\s*Lumen\b",
                r"Luminous[:\s]+Flux[:\s]+(\d+)\s*Lumen",
                r"Light[:\s]+Output[:\s]+(\d+)\s*Lumen",
                r"(\d+)\s*lm\b",
                # German patterns (fallback)
                r"Lichtstrom[:\s]+(\d+)\s*Lumen",
            ],
            "beam_angle": [
                # English patterns (prioritized)
                r"(\d+(?:°|Grad))\b",
                r"Beam[:\s]+Angle[:\s]+(\d+(?:°|Grad))",
                r"Light[:\s]+Distribution[:\s]+(\d+(?:°|Grad))",
                r"Spread[:\s]+(\d+(?:°|Grad))",
                # German patterns (fallback)
                r"Abstrahlwinkel[:\s]+(\d+(?:°|Grad))",
                r"Öffnungswinkel[:\s]+(\d+(?:°|Grad))",
            ],
            "lebensdauer_stunden": [
                # English patterns (prioritized)
                r"(\d+)\s*Hours\b",
                r"Lifetime[:\s]+(\d+)\s*Hours",
                r"Service[:\s]+Life[:\s]+(\d+)\s*Hours",
                r"Operating[:\s]+Life[:\s]+(\d+)\s*Hours",
                r"(\d+)\s*h\b",
                # German patterns (fallback)
                r"(\d+)\s*Stunden",
                r"Lebensdauer[:\s]+(\d+)\s*Stunden",
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

    def run(self, text: str, source_pdf: str = "unknown.pdf") -> List[ProductSpecification]:
        """Parse text and extract product specifications"""
        try:
            # Split text into potential product sections
            products = self._split_into_products(text)

            parsed_products = []
            for i, product_text in enumerate(products):
                product_data = self._extract_product_data(product_text, i, source_pdf)
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

    def _extract_product_data(
        self, text: str, index: int, source_pdf: str = "unknown.pdf"
    ) -> ProductSpecification:
        """Extract product data from a text section"""
        try:
            data = {}

            # Extract basic information
            data["product_name"] = self._extract_product_name(text)

            # Try to extract SKU with improved logic
            sku = self._extract_field(text, "sku")
            if not sku or sku in ["describes", "unknown", "n/a"]:
                # Fallback: try to extract from filename or first line
                sku = self._extract_sku_fallback(text, source_pdf, index)

            data["sku"] = sku
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

            # Set full description and source
            data["full_description"] = text
            data["source_pdf"] = source_pdf  # Will be set by caller

            return ProductSpecification(**data)

        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    def _extract_sku_fallback(self, text: str, source_pdf: str, index: int) -> str:
        """Fallback method to extract SKU when normal patterns fail"""
        import re
        import os

        # Try to extract from filename first
        if source_pdf and source_pdf != "unknown.pdf":
            filename = os.path.basename(source_pdf)
            # Extract ZMP codes from filename
            zmp_match = re.search(r"ZMP[_\s]*(\d+)", filename)
            if zmp_match:
                return f"ZMP_{zmp_match.group(1)}"

            # Extract any alphanumeric code from filename
            code_match = re.search(r"([A-Z0-9]+)", filename)
            if code_match:
                return code_match.group(1)

        # Try to extract from first line of text
        first_line = text.split("\n")[0].strip()

        # Look for product codes at start of line
        start_match = re.search(r"^#\s*(\d+)", first_line)
        if start_match:
            return start_match.group(1)

        # Look for any 7+ digit number (likely product code)
        long_number = re.search(r"\b(\d{7,})\b", first_line)
        if long_number:
            return long_number.group(1)

        # Look for ZMP codes in text
        zmp_text_match = re.search(r"ZMP[_\s]*(\d+)", text)
        if zmp_text_match:
            return f"ZMP_{zmp_text_match.group(1)}"

        # Final fallback
        return f"UNKNOWN_{index}"

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
