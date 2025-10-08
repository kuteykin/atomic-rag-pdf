# tests/conftest.py

"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import Settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings"""
    return Settings(
        mistral_api_key="test_key",
        sqlite_path=f"{temp_dir}/test.db",
        qdrant_path=f"{temp_dir}/qdrant",
        pdf_directory=f"{temp_dir}/pdfs",
    )


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "product_name": "Test Leuchte",
        "sku": "TEST-001",
        "primary_product_number": "123456789",
        "watt": 100,
        "voltage": "230V",
        "color_temperature": "3000K",
        "lebensdauer_stunden": 50000,
        "application_area": "Büro",
        "full_description": "Test description for testing purposes",
        "source_pdf": "test.pdf",
    }
