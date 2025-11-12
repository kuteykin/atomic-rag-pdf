#!/bin/bash
# launch_streamlit.sh

echo "🚀 Launching Atomic RAG System Streamlit Frontend..."
echo ""

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if MISTRAL_API_KEY is set
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "⚠️  Warning: MISTRAL_API_KEY not set in environment"
    echo "   Please set MISTRAL_API_KEY: export MISTRAL_API_KEY='your_key_here'"
fi

echo "📋 System Information:"
echo "   • Project: Atomic RAG System"
echo "   • Frontend: Streamlit Web Interface"
echo "   • Backend: Multi-agent RAG pipeline"
echo "   • Storage: SQLite + Qdrant"
echo ""

echo "🌐 Starting Streamlit server..."
echo "   • URL: http://localhost:8501"
echo "   • Press Ctrl+C to stop"
echo ""

# Launch Streamlit using Poetry (recommended approach)
# Use poetry from PATH, or find it if not in PATH
POETRY_CMD=$(command -v poetry)
if [ -z "$POETRY_CMD" ]; then
    echo "❌ Error: poetry not found in PATH"
    echo "   Please install poetry or add it to your PATH"
    exit 1
fi

$POETRY_CMD run streamlit run streamlit_app.py --server.port 8501 --server.address localhost
