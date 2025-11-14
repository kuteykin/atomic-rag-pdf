# src/utils/schema_utils.py

from typing import Dict, List, Any, get_type_hints, get_origin, get_args
from pydantic import BaseModel
from pydantic.fields import FieldInfo
import logging

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """Utility for introspecting Pydantic schemas and generating database schemas"""

    @staticmethod
    def get_schema_info(model_class: type[BaseModel]) -> Dict[str, Any]:
        """
        Extract schema information from a Pydantic model

        Returns:
            Dict with 'required_fields', 'optional_fields', and 'sql_schema'
        """
        fields_info = model_class.model_fields
        required_fields = []
        optional_fields = []

        for field_name, field_info in fields_info.items():
            # Skip metadata fields that shouldn't be in user-editable schema
            if field_name in ["extracted_at", "full_description", "source_pdf"]:
                continue

            field_dict = SchemaIntrospector._field_to_dict(field_name, field_info)

            if field_info.is_required():
                required_fields.append(field_dict)
            else:
                optional_fields.append(field_dict)

        return {
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "sql_schema": SchemaIntrospector.generate_sql_schema(model_class),
        }

    @staticmethod
    def _field_to_dict(field_name: str, field_info: FieldInfo) -> Dict[str, Any]:
        """Convert a Pydantic field to a dictionary with type and description"""

        # Get the annotation (type)
        annotation = field_info.annotation

        # Handle Optional types
        origin = get_origin(annotation)
        if origin is type(None) or str(origin) == "typing.Union":
            args = get_args(annotation)
            if args:
                # Get the non-None type
                annotation = next((arg for arg in args if arg is not type(None)), args[0])

        # Convert Python type to schema type string
        type_str = SchemaIntrospector._python_type_to_schema_type(annotation)

        return {
            "name": field_name,
            "type": type_str,
            "description": field_info.description or f"{field_name} field",
            "required": field_info.is_required(),
            "default": field_info.default if field_info.default is not None else None,
        }

    @staticmethod
    def _python_type_to_schema_type(python_type) -> str:
        """Convert Python type annotation to schema type string"""
        origin = get_origin(python_type)

        # Handle list/array types
        if origin is list:
            args = get_args(python_type)
            if args:
                inner_type = SchemaIntrospector._python_type_to_schema_type(args[0])
                return f"array of {inner_type}"
            return "array"

        # Handle basic types
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
        }

        return type_map.get(python_type, str(python_type))

    @staticmethod
    def generate_sql_schema(model_class: type[BaseModel]) -> Dict[str, str]:
        """
        Generate SQL schema from Pydantic model

        Returns:
            Dict mapping field names to SQL type strings
        """
        fields_info = model_class.model_fields
        sql_schema = {}

        for field_name, field_info in fields_info.items():
            sql_type = SchemaIntrospector._pydantic_to_sql_type(field_info)
            sql_schema[field_name] = sql_type

        return sql_schema

    @staticmethod
    def _pydantic_to_sql_type(field_info: FieldInfo) -> str:
        """Convert Pydantic field to SQL type"""
        annotation = field_info.annotation

        # Handle Optional types
        origin = get_origin(annotation)
        is_optional = False

        if origin is type(None) or str(origin) == "typing.Union":
            args = get_args(annotation)
            if args and type(None) in args:
                is_optional = True
                annotation = next((arg for arg in args if arg is not type(None)), args[0])

        # Check if it's a list
        origin = get_origin(annotation)
        if origin is list:
            sql_type = "TEXT"  # Store as JSON string
        else:
            # Map Python types to SQL types
            type_map = {
                str: "TEXT",
                int: "INTEGER",
                float: "REAL",
                bool: "INTEGER",  # SQLite doesn't have boolean
            }
            sql_type = type_map.get(annotation, "TEXT")

        # Add NOT NULL constraint if required
        if field_info.is_required() and not is_optional:
            sql_type += " NOT NULL"

        return sql_type

    @staticmethod
    def get_qdrant_metadata_fields(model_class: type[BaseModel]) -> List[str]:
        """
        Get list of fields that should be stored as Qdrant metadata

        Returns:
            List of field names to include in Qdrant payload
        """
        # Common fields to include in vector search metadata
        priority_fields = [
            "product_name",
            "sku",
            "wattage",
            "lifetime_hours",
            "voltage",
            "color_temperature",
            "luminous_flux",
            "application_area",
        ]

        # Get all fields from the model
        all_fields = list(model_class.model_fields.keys())

        # Return priority fields that exist in the model
        metadata_fields = [f for f in priority_fields if f in all_fields]

        # Add source_pdf if not already included
        if "source_pdf" not in metadata_fields:
            metadata_fields.append("source_pdf")

        return metadata_fields


def format_schema_for_display(schema_info: Dict[str, Any]) -> str:
    """Format schema info for display in UI or logs"""
    lines = ["=" * 70, "Product Schema", "=" * 70, ""]

    lines.append("REQUIRED FIELDS:")
    for field in schema_info["required_fields"]:
        lines.append(f"  • {field['name']} ({field['type']})")
        lines.append(f"    {field['description']}")
        lines.append("")

    lines.append("OPTIONAL FIELDS:")
    for field in schema_info["optional_fields"]:
        lines.append(f"  • {field['name']} ({field['type']})")
        lines.append(f"    {field['description']}")
        lines.append("")

    return "\n".join(lines)
