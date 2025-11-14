# Logging System Documentation

## Overview

The Atomic RAG System now includes a comprehensive logging system with component-based separation and daily log rotation. This document explains how the logging system works and how to use it.

## Features

✅ **Component-based log separation** - Separate log files for agents, tools, database, API, and Streamlit
✅ **Daily log rotation** - New files created each day with date-based naming
✅ **Size-based rotation** - 10MB per file with 5 backup copies
✅ **Detailed formatting** - Includes timestamp, logger name, level, file, line number, and message
✅ **Console + File output** - Logs to both console (for development) and files (for production)
✅ **Exception tracking** - Full stack traces for all exceptions
✅ **Configurable log levels** - Set different levels per component

## Log File Organization

All logs are stored in `./logs/` with the following structure:

```
logs/
├── app_2025-11-13.log          # Main application log (everything)
├── main_2025-11-13.log         # CLI commands (load, search, test)
├── agents_2025-11-13.log       # Data Loader, Research, QA agents
├── tools_2025-11-13.log        # OCR, translation, search, parser tools
├── database_2025-11-13.log     # SQLite and Qdrant operations
├── api_2025-11-13.log          # Mistral API calls
└── streamlit_2025-11-13.log    # Streamlit web interface
```

## Usage

### Basic Usage (Already Configured)

The logging system is automatically initialized in:
- **main.py** - CLI application
- **streamlit_app.py** - Web interface
- **scripts/*.py** - Utility scripts

You don't need to do anything - just run your application normally!

### Adding Logging to New Code

```python
import logging

# Get logger for your module
logger = logging.getLogger(__name__)

# Use it
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")

# Log exceptions with full traceback
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
```

### Manual Configuration

```python
from src.utils.logging_config import setup_logging

# Enable both console and file logging
setup_logging(console=True, file=True)

# File logging only (for production)
setup_logging(console=False, file=True)
```

### Change Log Level Dynamically

```python
from src.utils.logging_config import LoggingConfig
import logging

# Set root logger to DEBUG
LoggingConfig.set_level(logging.DEBUG)

# Set specific component to WARNING
LoggingConfig.set_level(logging.WARNING, component="tools")

# Set specific module to ERROR
LoggingConfig.set_level(logging.ERROR, component="src.tools.translation_tools")
```

### Cleanup Old Logs

```python
from src.utils.logging_config import LoggingConfig

# Remove logs older than 7 days
LoggingConfig.cleanup_old_logs(days_to_keep=7)
```

## Component Mapping

The logging system routes logs to appropriate files based on logger names:

| Logger Name Pattern | Log File | Purpose |
|---------------------|----------|---------|
| `__main__`, `main` | `main_*.log` | CLI commands |
| `src.agents.*` | `agents_*.log` | All agent operations |
| `src.tools.*` | `tools_*.log` | Tool executions |
| `src.utils.db_manager`, `src.utils.embedding_manager` | `database_*.log` | Database operations |
| `requests`, `urllib3`, `src.api.*` | `api_*.log` | External API calls |
| `streamlit_app`, `streamlit` | `streamlit_*.log` | Web interface |
| All loggers | `app_*.log` | Complete log |

## Log Format

```
2025-11-13 22:37:43,979 - src.agents.research_agent - INFO - [research_agent.py:76] - Query classified as: SEMANTIC
```

Format breakdown:
- `2025-11-13 22:37:43,979` - Timestamp with milliseconds
- `src.agents.research_agent` - Logger name (module path)
- `INFO` - Log level
- `[research_agent.py:76]` - File and line number
- `Query classified as: SEMANTIC` - Log message

## Log Levels

| Level | When to Use |
|-------|-------------|
| **DEBUG** | Detailed diagnostic information (not in production) |
| **INFO** | General informational messages (default) |
| **WARNING** | Warning messages for potential issues |
| **ERROR** | Error messages when operation fails |
| **CRITICAL** | Critical errors that may crash the system |

## Testing Logging

Run the test script to verify logging is working:

```bash
python test_logging.py
```

This will:
1. Generate test log entries for all components
2. Create log files in `./logs/`
3. Display which log files were created
4. Show sample output on console

## Monitoring Logs

### View Logs in Real-Time

```bash
# Watch main application log
tail -f logs/app_$(date +%Y-%m-%d).log

# Watch specific component
tail -f logs/agents_$(date +%Y-%m-%d).log

# Follow multiple logs
tail -f logs/*.log
```

### Search Logs

```bash
# Find all errors today
grep "ERROR" logs/app_$(date +%Y-%m-%d).log

# Find specific query
grep "Search initiated" logs/main_$(date +%Y-%m-%d).log

# Count warnings by component
grep "WARNING" logs/tools_*.log | wc -l
```

## Fallback Mechanisms & Error Tracking

The logging system helps track fallback mechanisms:

### Example: Translation Fallback

When translation fails, you'll see in `tools_*.log`:
```
ERROR - Error translating to English: ConnectionError
INFO - Returning original text as fallback
```

### Example: Query Classification Fallback

When LLM classification fails, you'll see in `tools_*.log`:
```
ERROR - Error in LLM classification: APIError
INFO - Falling back to SEMANTIC search with simple keyword extraction
```

### Example: Data Loading Partial Failure

In `agents_*.log`:
```
INFO - Processing PDF: product_001.pdf
ERROR - OCR failed for product_001.pdf: APITimeout
INFO - Skipping product_001.pdf, continuing with next file
INFO - Processing complete - Success: 99, Failed: 1
```

## Configuration

All configuration is in [src/utils/logging_config.py](src/utils/logging_config.py):

```python
class LoggingConfig:
    LOG_DIR = Path("./logs")          # Log directory
    DEFAULT_LEVEL = logging.INFO      # Default log level
    CONSOLE_LEVEL = logging.INFO      # Console log level
    FILE_LEVEL = logging.DEBUG        # File log level (more verbose)

    # Maximum file size before rotation (10MB)
    maxBytes = 10 * 1024 * 1024

    # Number of backup files to keep
    backupCount = 5
```

## Docker Considerations

When running in Docker:

1. **Mount logs directory as volume:**
```bash
docker run -v ./logs:/app/logs atomic-rag-system
```

2. **Set unbuffered output:**
```bash
docker run -e PYTHONUNBUFFERED=1 atomic-rag-system
```

3. **Access logs from host:**
```bash
docker exec -it <container> tail -f /app/logs/app_$(date +%Y-%m-%d).log
```

## Best Practices

### DO:
✅ Use appropriate log levels (INFO for normal, ERROR for failures)
✅ Include context in log messages (query, file name, user ID)
✅ Use `logger.exception()` for exceptions (includes stack trace)
✅ Log before and after critical operations
✅ Clean up old logs regularly

### DON'T:
❌ Log sensitive data (API keys, passwords, PII)
❌ Log at DEBUG level in production (too verbose)
❌ Log inside tight loops (performance impact)
❌ Commit log files to git (already gitignored)
❌ Use `print()` instead of `logger` for application logic

## Troubleshooting

### Problem: No logs are generated

**Solution:**
- Check logs directory exists and is writable: `ls -la logs/`
- Verify logging is initialized: `grep "Logging initialized" logs/app_*.log`
- Check code imports: `from src.utils.logging_config import setup_logging`

### Problem: Logs appear in wrong file

**Solution:**
- Check logger name matches component pattern
- Use `logger = logging.getLogger(__name__)` not hardcoded names
- Review component mapping in `LoggingConfig.COMPONENTS`

### Problem: Log files too large

**Solution:**
- Increase rotation in `logging_config.py`: `maxBytes = 50 * 1024 * 1024`
- Reduce log level: `LoggingConfig.set_level(logging.WARNING)`
- Clean old logs: `LoggingConfig.cleanup_old_logs(days_to_keep=3)`

### Problem: Missing logs from specific module

**Solution:**
- Check module is using `logger = logging.getLogger(__name__)`
- Verify logging is setup before module import
- Check log level isn't filtering messages

## Future Enhancements

Potential improvements:
- [ ] JSON-formatted logs for machine parsing
- [ ] Log aggregation to external service (e.g., ELK stack)
- [ ] Real-time log streaming endpoint
- [ ] Automatic log compression for old files
- [ ] Performance metrics logging
- [ ] User action audit trail

## Related Files

- [src/utils/logging_config.py](src/utils/logging_config.py) - Main logging configuration
- [logs/README.md](logs/README.md) - Logs directory documentation
- [test_logging.py](test_logging.py) - Logging test script
- [main.py](main.py) - CLI with logging
- [streamlit_app.py](streamlit_app.py) - Web interface with logging
