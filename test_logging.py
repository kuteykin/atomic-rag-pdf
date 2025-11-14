#!/usr/bin/env python3
"""
Quick test script to verify logging configuration with folder structure
Tests that logs are written to separate component subdirectories
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logging_config import setup_logging, get_logger
import logging

def test_logging():
    """Test logging across different components with folder structure"""
    print("Testing logging system with folder structure...")
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

    # Test streamlit logger
    streamlit_logger = get_logger("streamlit_app")
    streamlit_logger.info("Streamlit application test message")

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

    logs_dir = Path("./logs")

    # Main log in root
    print(f"\n📄 Main log (in {logs_dir.absolute()}):")
    main_log = logs_dir / f"app_{today}.log"
    if main_log.exists():
        size = main_log.stat().st_size
        print(f"  ✓ app_{today}.log ({size} bytes)")
    else:
        print(f"  ✗ app_{today}.log (not found)")

    # Component logs in subdirectories
    components = {
        "main": "main",
        "agents": "agents",
        "tools": "tools",
        "api": "api",
        "database": "database",
        "streamlit": "streamlit"
    }

    print(f"\n📁 Component logs (in subdirectories):")
    for component_name, subdir_name in components.items():
        subdir = logs_dir / subdir_name
        log_file = subdir / f"{today}.log"

        if subdir.exists() and log_file.exists():
            size = log_file.stat().st_size
            print(f"  ✓ {subdir_name}/{today}.log ({size} bytes)")
        elif subdir.exists():
            print(f"  ⚠ {subdir_name}/{today}.log (directory exists, no log file yet)")
        else:
            print(f"  ✗ {subdir_name}/ (directory not found)")

    print("\n📂 Directory structure:")
    print(f"logs/")
    print(f"  ├── app_{today}.log           (main combined log)")
    print(f"  ├── main/")
    print(f"  │   └── {today}.log           (CLI commands)")
    print(f"  ├── agents/")
    print(f"  │   └── {today}.log           (agent operations)")
    print(f"  ├── tools/")
    print(f"  │   └── {today}.log           (tool execution)")
    print(f"  ├── api/")
    print(f"  │   └── {today}.log           (API calls)")
    print(f"  ├── database/")
    print(f"  │   └── {today}.log           (database operations)")
    print(f"  └── streamlit/")
    print(f"      └── {today}.log           (web interface)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_logging()
