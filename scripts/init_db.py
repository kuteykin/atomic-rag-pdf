# scripts/init_db.py

"""
Initialize databases for the Atomic RAG System
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.db_manager import DatabaseManager
from src.tools.storage_tools import QdrantStorageTool, QdrantStorageToolConfig
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize databases"""
    print("🔄 Initializing databases...")

    try:
        # Initialize SQLite database
        print("📊 Initializing SQLite database...")
        db_manager = DatabaseManager(settings.sqlite_path)
        stats = db_manager.get_stats()
        print(f"✅ SQLite database ready at {settings.sqlite_path}")
        print(f"   Products: {stats['total_products']}")
        print(f"   PDFs: {stats['total_pdfs']}")

        # Initialize Qdrant collection
        print("🔍 Initializing Qdrant collection...")
        qdrant_tool = QdrantStorageTool(QdrantStorageToolConfig(qdrant_path=settings.qdrant_path))
        info = qdrant_tool.get_collection_info()
        print(f"✅ Qdrant collection ready at {settings.qdrant_path}")
        print(f"   Points: {info.get('points_count', 0)}")

        print("\n🎉 Database initialization complete!")

    except Exception as e:
        logger.error(f"Error initializing databases: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
