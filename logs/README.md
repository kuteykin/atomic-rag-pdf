# Logs Directory

This directory contains application logs for the Atomic RAG System.

## Directory Structure

Logs are automatically organized into component-specific folders with daily rotation:

```
logs/
├── app_YYYY-MM-DD.log          # Main combined log (all components)
├── main/                       # CLI application logs
│   └── YYYY-MM-DD.log
├── agents/                     # Agent system logs
│   └── YYYY-MM-DD.log
├── tools/                      # Tool execution logs
│   └── YYYY-MM-DD.log
├── api/                        # External API calls
│   └── YYYY-MM-DD.log
├── database/                   # Database operations
│   └── YYYY-MM-DD.log
└── streamlit/                  # Web interface logs
    └── YYYY-MM-DD.log
```

## Log Files

### Main Log (Root Directory)
- **`app_YYYY-MM-DD.log`** - Complete application log
  - Contains all log entries from all components
  - Useful for overall system monitoring
  - Located in logs root directory

### Component Logs (Subdirectories)

#### **`main/YYYY-MM-DD.log`** - CLI Application
  - Command execution (load, search, test)
  - High-level application flow
  - User interactions via CLI

#### **`agents/YYYY-MM-DD.log`** - Agent Operations
  - Data Loader Agent operations
  - Research Agent searches
  - QA Agent answer generation

#### **`tools/YYYY-MM-DD.log`** - Tool Execution
  - OCR processing
  - Translation operations
  - Search tools
  - Answer generation tools
  - Query classification

#### **`database/YYYY-MM-DD.log`** - Database Operations
  - SQLite queries and operations
  - Qdrant vector operations
  - Embedding generation

#### **`api/YYYY-MM-DD.log`** - External API Calls
  - Mistral API requests
  - API errors and timeouts
  - Rate limiting issues

#### **`streamlit/YYYY-MM-DD.log`** - Web Interface
  - User interactions
  - Search requests from web UI
  - Agent initialization

## Log Rotation

- **Daily rotation**: New log files created each day (YYYY-MM-DD format)
- **Size limit**: 10MB per file with 5 backup files
- **Retention**: Old logs should be cleaned up periodically (7-30 days recommended)

## Log Levels

Logs use standard Python logging levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (potential issues)
- **ERROR**: Error messages (operation failed but app continues)
- **CRITICAL**: Critical errors (system may be unstable)

## Log Format

```
YYYY-MM-DD HH:MM:SS,mmm - logger.name - LEVEL - [filename.py:line] - Message
```

Example:
```
2025-11-13 22:37:43,979 - src.agents.data_loader_agent - INFO - [data_loader_agent.py:141] - Data Loader Agent initialized
```

## Cleaning Old Logs

To manually clean logs older than 7 days:
```bash
find ./logs -name "*.log*" -mtime +7 -delete
```

Or use the Python utility:
```python
from src.utils.logging_config import LoggingConfig
LoggingConfig.cleanup_old_logs(days_to_keep=7)
```

## Troubleshooting

### No logs generated?
- Check that the application is using `setup_logging()` at startup
- Verify the logs directory has write permissions
- Check that `PYTHONUNBUFFERED=1` is set for Docker environments

### Logs not separated by component?
- The logging system routes logs based on logger names
- Ensure modules use `logger = logging.getLogger(__name__)`

### File size too large?
- Adjust `maxBytes` in [src/utils/logging_config.py](../src/utils/logging_config.py)
- Reduce log retention period
- Increase log level (e.g., WARNING instead of INFO)

## Privacy & Security

**Important**: Log files may contain:
- Query content (potentially sensitive)
- Product data
- System paths

Do NOT:
- Commit log files to git (already gitignored)
- Share logs publicly without redacting sensitive data
- Store logs with customer/production data without proper access control
