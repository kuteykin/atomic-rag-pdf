#!/bin/bash
# launch_streamlit.sh

echo "🚀 Launching Atomic RAG System Streamlit Frontend..."
echo ""

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please ensure MISTRAL_API_KEY is set."
    echo "   You can create .env file or set environment variables."
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
/home/drphyl/.local/bin/poetry run streamlit run streamlit_app.py --server.port 8501 --server.address localhost
