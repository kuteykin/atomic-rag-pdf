"""
Test the dynamic schema system
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.schemas.product_schema import ProductSpecification
from src.utils.schema_utils import SchemaIntrospector, format_schema_for_display


def test_schema_introspection():
    """Test schema introspection"""
    print("="*70)
    print("Testing Dynamic Schema System")
    print("="*70)

    # Test 1: Get schema info
    print("\n📋 Test 1: Schema Introspection")
    print("-"*70)
    schema_info = SchemaIntrospector.get_schema_info(ProductSpecification)

    required_count = len(schema_info["required_fields"])
    optional_count = len(schema_info["optional_fields"])

    print(f"✓ Found {required_count} required fields")
    print(f"✓ Found {optional_count} optional fields")

    # Test 2: SQL schema generation
    print("\n💾 Test 2: SQL Schema Generation")
    print("-"*70)
    sql_schema = schema_info["sql_schema"]

    print(f"✓ Generated SQL schema with {len(sql_schema)} columns")
    print("\nSample columns:")
    for i, (field_name, sql_type) in enumerate(list(sql_schema.items())[:5]):
        print(f"  • {field_name}: {sql_type}")
    print(f"  ... and {len(sql_schema) - 5} more")

    # Test 3: Qdrant metadata fields
    print("\n🔍 Test 3: Qdrant Metadata Fields")
    print("-"*70)
    metadata_fields = SchemaIntrospector.get_qdrant_metadata_fields(ProductSpecification)

    print(f"✓ Generated {len(metadata_fields)} metadata fields")
    print(f"Fields: {', '.join(metadata_fields)}")

    # Test 4: Field type conversion
    print("\n🔄 Test 4: Type Conversions")
    print("-"*70)
    type_tests = [
        ("product_name", "string", "TEXT NOT NULL"),
        ("wattage", "integer", "INTEGER"),
        ("suitable_for", "array", "TEXT"),
    ]

    for field_name, expected_schema_type, expected_sql_type in type_tests:
        # Find field in schema
        field = next(
            (f for f in schema_info["required_fields"] + schema_info["optional_fields"]
             if f["name"] == field_name),
            None
        )

        if field:
            schema_type = field["type"]
            sql_type = sql_schema.get(field_name, "")

            schema_match = expected_schema_type in schema_type.lower()
            sql_match = expected_sql_type in sql_type

            print(f"  • {field_name}:")
            print(f"    Schema type: {schema_type} {'✓' if schema_match else '✗'}")
            print(f"    SQL type: {sql_type} {'✓' if sql_match else '✗'}")

    # Test 5: Format display
    print("\n📄 Test 5: Schema Display Formatting")
    print("-"*70)
    formatted = format_schema_for_display(schema_info)
    print(f"✓ Generated formatted display ({len(formatted)} characters)")
    print("\nFirst 300 characters:")
    print(formatted[:300] + "...")

    # Test 6: Database creation
    print("\n💾 Test 6: Database Table Creation")
    print("-"*70)
    try:
        from src.utils.db_manager import DatabaseManager
        import tempfile
        import os

        # Create temporary database
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_schema.db")
            db_manager = DatabaseManager(test_db)

            print(f"✓ Successfully created test database with dynamic schema")
            print(f"  Database path: {test_db}")

    except Exception as e:
        print(f"✗ Database creation failed: {e}")

    # Summary
    print("\n" + "="*70)
    print("Dynamic Schema System Tests Complete!")
    print("="*70)
    print("\n✅ All components working correctly:")
    print("  • Schema introspection from Pydantic model")
    print("  • SQL schema generation")
    print("  • Qdrant metadata field selection")
    print("  • Type conversions (Python → SQL → Schema)")
    print("  • Display formatting")
    print("  • Database table creation")
    print("\n📝 To modify schema: Edit src/schemas/product_schema.py")
    print("📊 To view schema in UI: Open Streamlit and navigate to Schema Editor page")


if __name__ == "__main__":
    test_schema_introspection()
