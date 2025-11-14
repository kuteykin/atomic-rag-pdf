#!/usr/bin/env python3
"""
Quick test script to verify logging configuration
Tests that logs are written to separate component files
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logging_config import setup_logging, get_logger
import logging

def test_logging():
    """Test logging across different components"""
    print("Testing logging system...")
    print("=" * 80)

    # Setup logging
    setup_logging(console=True, file=True)

    # Test main logger
    main_logger = get_logger("__main__")
    main_logger.info("Main application logger test")
    main_logger.warning("This is a warning from main")

    # Test agents logger
    agent_logger = get_logger("src.agents.data_loader_agent")
    agent_logger.info("Data Loader Agent test message")
    agent_logger.error("Simulated agent error")

    # Test tools logger
    tool_logger = get_logger("src.tools.translation_tools")
    tool_logger.info("Translation tool test message")
    tool_logger.debug("Debug message from translation tool")

    # Test API logger
    api_logger = get_logger("src.api")
    api_logger.info("API logger test message")

    # Test database logger
    db_logger = get_logger("src.utils.db_manager")
    db_logger.info("Database manager test message")
    db_logger.warning("Simulated database warning")

    # Test exception logging
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        main_logger.exception("Caught test exception")

    print("=" * 80)
    print("Logging test complete!")
    print(f"\nCheck the following log files in ./logs/:")

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    log_files = [
        f"app_{today}.log",
        f"main_{today}.log",
        f"agents_{today}.log",
        f"tools_{today}.log",
        f"api_{today}.log",
        f"database_{today}.log",
    ]

    logs_dir = Path("./logs")
    print(f"\nExpected log files (in {logs_dir.absolute()}):")
    for log_file in log_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"  ✓ {log_file} ({size} bytes)")
        else:
            print(f"  ✗ {log_file} (not found)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_logging()
