# Multi-stage Dockerfile for Atomic RAG System
# Optimized for production with Poetry dependency management

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "mistralai>=0.4.0,<2.0.0" \
    "qdrant-client>=1.6.0,<2.0.0" \
    "sentence-transformers>=2.2.0,<3.0.0" \
    "transformers>=4.30.0,<5.0.0" \
    "tokenizers>=0.13.0,<1.0.0" \
    "numpy>=1.21.0,<2.0.0" \
    "scikit-learn>=1.3.0,<2.0.0" \
    "pydantic>=2.0.0,<3.0.0" \
    "python-dotenv>=1.0.0,<2.0.0" \
    "pydantic-settings>=2.0.0,<3.0.0" \
    "pypdf2>=3.0.0,<4.0.0" \
    "pillow>=9.0.0,<11.0.0" \
    "rich>=13.0.0,<14.0.0" \
    "typer>=0.9.0,<1.0.0" \
    "loguru>=0.7.0,<1.0.0" \
    "streamlit>=1.28.0,<2.0.0" \
    "requests>=2.31.0,<3.0.0" \
    "httpx>=0.25.0,<1.0.0"

# Stage 2: Runtime stage
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    # PDF processing
    libpoppler-cpp-dev \
    poppler-utils \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    # ML libraries (using available packages)
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    gfortran \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/storage /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - start Streamlit web interface
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
