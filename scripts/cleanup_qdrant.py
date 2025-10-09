#!/usr/bin/env python3
"""
Cleanup script for Qdrant storage issues
Removes stale lock files and resets Qdrant storage if needed
"""

import os
import sys
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_qdrant_locks():
    """Remove stale Qdrant lock files"""
    qdrant_path = Path(settings.qdrant_path)
    lock_file = qdrant_path / ".lock"

    if lock_file.exists():
        print(f"🔓 Removing stale lock file: {lock_file}")
        lock_file.unlink()
        print("✅ Lock file removed successfully")
    else:
        print("✅ No lock file found")


def reset_qdrant_storage():
    """Reset Qdrant storage (WARNING: This will delete all data)"""
    qdrant_path = Path(settings.qdrant_path)

    if qdrant_path.exists():
        print(f"⚠️  WARNING: This will delete all Qdrant data at {qdrant_path}")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() == "yes":
            print(f"🗑️  Removing Qdrant storage directory: {qdrant_path}")
            shutil.rmtree(qdrant_path)
            print("✅ Qdrant storage reset successfully")
        else:
            print("❌ Operation cancelled")
    else:
        print("✅ Qdrant storage directory doesn't exist")


def check_qdrant_status():
    """Check Qdrant storage status"""
    qdrant_path = Path(settings.qdrant_path)

    print(f"📊 Qdrant Storage Status:")
    print(f"   Path: {qdrant_path}")
    print(f"   Exists: {qdrant_path.exists()}")

    if qdrant_path.exists():
        lock_file = qdrant_path / ".lock"
        print(f"   Lock file exists: {lock_file.exists()}")

        if lock_file.exists():
            try:
                with open(lock_file, "r") as f:
                    lock_content = f.read().strip()
                print(f"   Lock content: {lock_content}")
            except Exception as e:
                print(f"   Lock content: Error reading - {e}")

        # Check collection directory
        collection_dir = qdrant_path / "collection"
        if collection_dir.exists():
            print(f"   Collection directory exists: {collection_dir.exists()}")
            print(f"   Collection files: {len(list(collection_dir.rglob('*')))}")


def main():
    """Main cleanup function"""
    import argparse

    parser = argparse.ArgumentParser(description="Qdrant storage cleanup utility")
    parser.add_argument("--cleanup-locks", action="store_true", help="Remove stale lock files")
    parser.add_argument(
        "--reset", action="store_true", help="Reset Qdrant storage (WARNING: deletes all data)"
    )
    parser.add_argument("--status", action="store_true", help="Check Qdrant storage status")

    args = parser.parse_args()

    if args.status:
        check_qdrant_status()
    elif args.cleanup_locks:
        cleanup_qdrant_locks()
    elif args.reset:
        reset_qdrant_storage()
    else:
        # Default: check status and cleanup locks if needed
        check_qdrant_status()
        print()
        cleanup_qdrant_locks()


if __name__ == "__main__":
    main()
