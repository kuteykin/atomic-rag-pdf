# src/utils/logging_config.py

"""
Centralized logging configuration for Atomic RAG System
Creates daily rotating logs separated by component (agents, tools, api, main)
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration with component-based separation"""

    LOG_DIR = Path("./logs")

    # Log components with separate subdirectories
    COMPONENTS = {
        "main": {
            "loggers": ["__main__", "main"],
            "subdir": "main"
        },
        "agents": {
            "loggers": ["src.agents"],
            "subdir": "agents"
        },
        "tools": {
            "loggers": ["src.tools"],
            "subdir": "tools"
        },
        "api": {
            "loggers": ["src.api", "requests", "urllib3"],
            "subdir": "api"
        },
        "database": {
            "loggers": ["src.utils.db_manager", "src.utils.embedding_manager"],
            "subdir": "database"
        },
        "streamlit": {
            "loggers": ["streamlit_app", "streamlit"],
            "subdir": "streamlit"
        },
    }

    # Log levels
    DEFAULT_LEVEL = logging.INFO
    CONSOLE_LEVEL = logging.INFO
    FILE_LEVEL = logging.DEBUG

    # Log format
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    _configured = False
    _loggers = {}

    @classmethod
    def setup_logging(cls, console_output: bool = True, file_output: bool = True) -> None:
        """
        Setup logging configuration for the entire application

        Args:
            console_output: Enable console logging
            file_output: Enable file logging with daily rotation
        """
        if cls._configured:
            return

        # Create main logs directory
        cls.LOG_DIR.mkdir(exist_ok=True)

        # Create component subdirectories
        for component_name, config in cls.COMPONENTS.items():
            subdir = cls.LOG_DIR / config["subdir"]
            subdir.mkdir(exist_ok=True)
            # Create .gitkeep file to preserve directory structure
            gitkeep = subdir / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

        # Get today's date for log file naming
        today = datetime.now().strftime("%Y-%m-%d")

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(cls.DEFAULT_LEVEL)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Console handler (if enabled)
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(cls.CONSOLE_LEVEL)
            console_handler.setFormatter(logging.Formatter(cls.SIMPLE_FORMAT))
            root_logger.addHandler(console_handler)

        # File handler for main application log (if enabled)
        if file_output:
            main_log_file = cls.LOG_DIR / f"app_{today}.log"
            main_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=5,
                encoding="utf-8"
            )
            main_handler.setLevel(cls.FILE_LEVEL)
            main_handler.setFormatter(logging.Formatter(cls.DETAILED_FORMAT))
            root_logger.addHandler(main_handler)

        # Setup component-specific loggers
        if file_output:
            cls._setup_component_loggers(today)

        cls._configured = True

        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info("=" * 80)
        logger.info(f"Logging initialized - Date: {today}")
        logger.info(f"Log directory: {cls.LOG_DIR.absolute()}")
        logger.info(f"Console output: {console_output}, File output: {file_output}")
        logger.info("=" * 80)

    @classmethod
    def _setup_component_loggers(cls, today: str) -> None:
        """Setup separate log files for each component in subdirectories"""

        for component_name, config in cls.COMPONENTS.items():
            subdir = cls.LOG_DIR / config["subdir"]
            log_file = subdir / f"{today}.log"

            # Create file handler for this component
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=5,
                encoding="utf-8"
            )
            handler.setLevel(cls.FILE_LEVEL)
            handler.setFormatter(logging.Formatter(cls.DETAILED_FORMAT))

            # Attach handler to all loggers matching the prefix
            for prefix in config["loggers"]:
                logger = logging.getLogger(prefix)

                # Avoid duplicate handlers
                if not any(isinstance(h, type(handler)) and h.baseFilename == handler.baseFilename
                          for h in logger.handlers):
                    logger.addHandler(handler)

                cls._loggers[prefix] = logger

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with proper configuration

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        if not cls._configured:
            cls.setup_logging()

        return logging.getLogger(name)

    @classmethod
    def set_level(cls, level: int, component: Optional[str] = None) -> None:
        """
        Change logging level dynamically

        Args:
            level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
            component: Optional component name to target, or None for root logger
        """
        if component:
            if component in cls.COMPONENTS:
                for prefix in cls.COMPONENTS[component]["loggers"]:
                    logger = logging.getLogger(prefix)
                    logger.setLevel(level)
            else:
                logging.getLogger(component).setLevel(level)
        else:
            logging.getLogger().setLevel(level)

    @classmethod
    def cleanup_old_logs(cls, days_to_keep: int = 7) -> None:
        """
        Remove log files older than specified days from all subdirectories

        Args:
            days_to_keep: Number of days to keep logs
        """
        import time

        if not cls.LOG_DIR.exists():
            return

        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 86400)  # 86400 seconds = 1 day

        deleted_count = 0

        # Clean main directory logs
        for log_file in cls.LOG_DIR.glob("*.log*"):
            if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to delete old log file {log_file}: {e}")

        # Clean component subdirectory logs
        for component_name, config in cls.COMPONENTS.items():
            subdir = cls.LOG_DIR / config["subdir"]
            if subdir.exists():
                for log_file in subdir.glob("*.log*"):
                    if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                        try:
                            log_file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger = logging.getLogger(__name__)
                            logger.error(f"Failed to delete old log file {log_file}: {e}")

        if deleted_count > 0:
            logger = logging.getLogger(__name__)
            logger.info(f"Cleaned up {deleted_count} old log file(s)")


# Convenience function for quick setup
def setup_logging(console: bool = True, file: bool = True) -> None:
    """
    Quick setup function for logging

    Args:
        console: Enable console output
        file: Enable file output
    """
    LoggingConfig.setup_logging(console_output=console, file_output=file)


# Convenience function for getting logger
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return LoggingConfig.get_logger(name)
