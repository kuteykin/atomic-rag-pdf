# Single-container Dockerfile for Atomic RAG System
# Backend + Streamlit Frontend in one container
# Optimized for Python 3.10 with CPU-only ML models
# 
# REQUIRED: MISTRAL_API_KEY environment variable must be provided at runtime
# Usage: docker run -e MISTRAL_API_KEY=your_key atomic-rag:latest

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.3

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/storage /app/data/pdfs && \
    chown -R appuser:appuser /app/storage /app/data/pdfs

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

# Default command: Initialize databases and start Streamlit
CMD ["sh", "-c", "poetry run python scripts/init_db.py && poetry run streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]
