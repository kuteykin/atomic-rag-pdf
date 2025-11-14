# Logging Quick Start Guide

## TL;DR

✅ **Logging is already configured!** Just run your app normally.

📁 **Logs location:** `./logs/`

📊 **View logs in real-time:**
```bash
tail -f logs/app_$(date +%Y-%m-%d).log
```

## Log Files (Daily Rotation)

| File | Contains |
|------|----------|
| `app_YYYY-MM-DD.log` | Everything (complete log) |
| `main_YYYY-MM-DD.log` | CLI commands (search, load, test) |
| `agents_YYYY-MM-DD.log` | Agent operations (Data Loader, Research, QA) |
| `tools_YYYY-MM-DD.log` | Tool operations (OCR, translation, search, classification) |
| `database_YYYY-MM-DD.log` | Database operations (SQLite, Qdrant) |
| `api_YYYY-MM-DD.log` | External API calls (Mistral) |
| `streamlit_YYYY-MM-DD.log` | Web interface (Streamlit) |

## Common Commands

### View Today's Logs

```bash
# All logs
cat logs/app_$(date +%Y-%m-%d).log

# Agents only
cat logs/agents_$(date +%Y-%m-%d).log

# Errors only
grep ERROR logs/app_$(date +%Y-%m-%d).log

# Follow in real-time
tail -f logs/app_$(date +%Y-%m-%d).log
```

### Search Logs

```bash
# Find specific query
grep "Searching for" logs/main_*.log

# Find all errors
grep -r "ERROR" logs/

# Find translation events
grep "Translation" logs/tools_*.log

# Find API failures
grep "API error" logs/api_*.log
```

### Clean Old Logs

```bash
# Remove logs older than 7 days
find logs/ -name "*.log*" -mtime +7 -delete

# Or use Python
python -c "from src.utils.logging_config import LoggingConfig; LoggingConfig.cleanup_old_logs(7)"
```

## Adding Logging to Your Code

```python
import logging

# Get logger (use __name__ for automatic naming)
logger = logging.getLogger(__name__)

# Log messages
logger.info("This worked!")
logger.warning("This might be a problem")
logger.error("This failed")

# Log exceptions with full traceback
try:
    risky_operation()
except Exception as e:
    logger.exception(f"Operation failed: {e}")
```

## Debugging with Logs

### Problem: Search returns no results

```bash
# Check query classification
grep "Query classified as" logs/tools_*.log | tail -1

# Check search execution
grep "Search completed" logs/agents_*.log | tail -1

# Check translation
grep "Translation" logs/tools_*.log | tail -1
```

### Problem: PDF loading fails

```bash
# Check what failed
grep "ERROR" logs/agents_*.log | grep -i pdf

# Check OCR issues
grep "OCR" logs/tools_*.log | grep ERROR

# Check API issues
grep "ERROR" logs/api_*.log
```

### Problem: Slow performance

```bash
# Check timestamps to find bottlenecks
grep "Query:" logs/main_*.log | tail -1
grep "Answer generated" logs/main_*.log | tail -1

# Check API latency
grep "Mistral API" logs/api_*.log
```

## Log Levels

| Level | What It Means | Example |
|-------|---------------|---------|
| DEBUG | Detailed debug info | "Vector embedding: [0.123, ...]" |
| INFO | Normal operation | "Search completed - Found 5 results" |
| WARNING | Potential issue | "Translation failed, using original" |
| ERROR | Operation failed | "PDF processing failed: timeout" |
| CRITICAL | System failure | "Database connection lost" |

## Test Logging

Verify logging is working:

```bash
python test_logging.py
```

Expected output:
```
Testing logging system...
...
Expected log files (in ./logs):
  ✓ app_2025-11-13.log (1887 bytes)
  ✓ main_2025-11-13.log (502 bytes)
  ✓ agents_2025-11-13.log (228 bytes)
  ✓ tools_2025-11-13.log (116 bytes)
  ✓ api_2025-11-13.log (90 bytes)
  ✓ database_2025-11-13.log (218 bytes)
```

## Configuration

Change log level (for debugging):

```python
from src.utils.logging_config import LoggingConfig
import logging

# More verbose (DEBUG level)
LoggingConfig.set_level(logging.DEBUG)

# Less verbose (WARNING level)
LoggingConfig.set_level(logging.WARNING)

# Specific component only
LoggingConfig.set_level(logging.DEBUG, component="tools")
```

## Full Documentation

See [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md) for complete documentation.

## Questions?

- **Where are logs stored?** `./logs/` directory
- **How long are logs kept?** Forever (clean manually or with script)
- **How large can logs get?** 10MB per file, then rotates with 5 backups
- **Are logs in git?** No, `.gitignore` excludes them
- **Can I disable console output?** Yes: `setup_logging(console=False, file=True)`
