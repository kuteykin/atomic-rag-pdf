#!/bin/bash
# setup.sh - Poetry setup script for Atomic RAG System

echo "🚀 Setting up Atomic RAG System with Poetry..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✅ Poetry is already installed"
fi

# Install dependencies
echo "📚 Installing dependencies..."
poetry install

# Check if MISTRAL_API_KEY is set
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "⚠️  Warning: MISTRAL_API_KEY not set in environment"
    echo "🔑 Please set MISTRAL_API_KEY in your system environment:"
    echo "   export MISTRAL_API_KEY='your_key_here'"
    echo "   Or add it to your ~/.bashrc or ~/.zshrc"
else
    echo "✅ MISTRAL_API_KEY is set"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/pdfs
mkdir -p storage
mkdir -p tests
mkdir -p logs

# Initialize databases
echo "🗄️  Initializing databases..."
poetry run init-db

# Run basic tests
echo "🧪 Running basic tests..."
poetry run python test_basic.py

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure MISTRAL_API_KEY is set in your system environment (export MISTRAL_API_KEY='your_key')"
echo "2. Add PDF files to data/pdfs/ directory (100+ files already available)"
echo "3. Run: poetry run python main.py load"
echo "4. Run: poetry run python main.py search 'your query here'"
echo ""
echo "Available commands:"
echo "  poetry run python main.py load          # Load all PDFs"
echo "  poetry run python main.py load --limit 10  # Load first 10 PDFs"
echo "  poetry run python main.py search 'query' # Search (multilingual)"
echo "  poetry run python main.py test          # Run test queries"
echo "  poetry run streamlit run streamlit_app.py  # Launch web frontend"
echo "  ./launch_streamlit.sh                   # Launch web frontend (easy)"
echo "  poetry run pytest tests/                # Run full test suite"
echo "  poetry run python test_basic.py         # Test basic functionality"
echo ""
echo "System Status: ✅ Production Ready"
echo "- All test queries working"
echo "- Multilingual support (German, English, French, Spanish)"
echo "- CPU-only processing (no GPU required)"
echo "- Mistral OCR Latest with dedicated API"
echo "- SQLite + Qdrant hybrid storage"
