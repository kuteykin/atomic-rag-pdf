# streamlit_app.py

"""
Streamlit Frontend for Atomic RAG System
Multi-agent PDF search system with web interface
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time
import json
import logging
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Initialize logging BEFORE any other imports
from src.utils.logging_config import setup_logging
setup_logging(console=False, file=True)  # Disable console for Streamlit, keep file logging
logger = logging.getLogger(__name__)

# Import our agents
from src.agents.data_loader_agent import DataLoaderAgent, DataLoaderAgentConfig
from src.agents.research_agent import ResearchAgent, ResearchAgentConfig
from src.agents.qa_agent import QualityAssuranceAgent, QAAgentConfig
from src.config.settings import settings
from src.utils.model_info import get_actual_model_info, get_model_status, get_model_capabilities

# Log Streamlit startup
logger.info("=" * 80)
logger.info("Streamlit application started")
logger.info(f"Working directory: {os.getcwd()}")
logger.info("=" * 80)

# Page configuration
st.set_page_config(
    page_title="Atomic RAG System", page_icon="🔍", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables"""
    if "agents_initialized" not in st.session_state:
        st.session_state.agents_initialized = False
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = "Ready"
    if "last_search_results" not in st.session_state:
        st.session_state.last_search_results = None
    if "processing_progress" not in st.session_state:
        st.session_state.processing_progress = 0


def initialize_agents():
    """Initialize the RAG agents"""
    try:
        if not st.session_state.agents_initialized:
            with st.spinner("Initializing RAG agents..."):
                # Initialize agents
                research_config = ResearchAgentConfig()
                qa_config = QAAgentConfig()

                st.session_state.research_agent = ResearchAgent(research_config)
                st.session_state.qa_agent = QualityAssuranceAgent(qa_config)
                st.session_state.agents_initialized = True

            st.success("✅ RAG agents initialized successfully!")
            return True
    except Exception as e:
        st.error(f"❌ Error initializing agents: {e}")
        return False


def load_pdfs_batch(limit: int = 10) -> Dict[str, Any]:
    """Load and process PDFs in batch"""
    try:
        # Initialize data loader agent
        loader_config = DataLoaderAgentConfig(pdf_directory="./data/pdfs")
        loader_agent = DataLoaderAgent(loader_config)

        # Process PDFs with limit
        results = loader_agent.process_directory(limit=limit)

        return results
    except Exception as e:
        st.error(f"❌ Error processing PDFs: {e}")
        return {"error": str(e)}


def search_query(query: str) -> Dict[str, Any]:
    """Search for information using the RAG system"""
    logger.info(f"Streamlit search initiated - Query: {query}")
    try:
        if not st.session_state.agents_initialized:
            logger.error("Search attempted but agents not initialized")
            st.error("❌ Please initialize agents first!")
            return {"error": "Agents not initialized"}

        # Execute search
        logger.info("Executing research agent search")
        search_results = st.session_state.research_agent.search(query)
        logger.info(f"Search completed - Query type: {search_results.get('query_type')}, Results: {search_results.get('total_results')}")

        # Generate answer
        logger.info("Generating answer with QA agent")
        answer = st.session_state.qa_agent.generate_answer(query, search_results)
        logger.info(f"Answer generated - Confidence: {answer.get('confidence_score', 0):.2%}")

        return answer
    except Exception as e:
        logger.exception(f"Error during Streamlit search: {e}")
        st.error(f"❌ Error during search: {e}")
        return {"error": str(e)}


def display_search_results(results: Dict[str, Any]):
    """Display search results in a formatted way"""
    if "error" in results:
        st.error(f"❌ {results['error']}")
        return

    # Main answer
    st.markdown("### 💡 Answer")
    st.markdown(f"**Query:** {results.get('query', 'N/A')}")

    # Show translation info if applicable
    if results.get("translation_needed"):
        st.info(f"🌐 **Language detected:** {results['detected_language']}")
        st.info(f"🔄 **Translated query:** {results['english_query']}")

    # Display the answer
    st.markdown(f"**Answer:** {results.get('answer', 'No answer generated')}")

    # Metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Confidence", f"{results.get('confidence_score', 0):.1%}")

    with col2:
        st.metric("Completeness", f"{results.get('completeness_score', 0):.1%}")

    with col3:
        st.metric("Accuracy", f"{results.get('accuracy_score', 0):.1%}")

    # Sources
    st.markdown("### 📚 Sources Used")
    sources_used = results.get("sources_used", 0)
    st.write(f"**Number of sources:** {sources_used}")

    # Search strategy
    metadata = results.get("metadata", {})
    search_strategy = metadata.get("search_strategy", "Unknown")
    st.write(f"**Search strategy:** {search_strategy}")

    # Warnings
    if results.get("warnings"):
        st.markdown("### ⚠️ Warnings")
        for warning in results["warnings"]:
            st.warning(f"• {warning}")


def main():
    """Main Streamlit application"""

    # Initialize session state
    initialize_session_state()

    # Header
    st.markdown('<h1 class="main-header">🔍 Atomic RAG System</h1>', unsafe_allow_html=True)
    st.markdown("**Multi-agent PDF search system with multilingual support**")

    # Sidebar
    st.sidebar.title("🎛️ Control Panel")

    # System status
    st.sidebar.markdown("### 📊 System Status")
    st.sidebar.write(f"**Status:** {st.session_state.processing_status}")
    st.sidebar.write(
        f"**Agents:** {'✅ Initialized' if st.session_state.agents_initialized else '❌ Not initialized'}"
    )

    # Initialize agents button
    if st.sidebar.button("🚀 Initialize Agents", type="primary"):
        initialize_agents()

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📄 PDF Processing", "🔍 Search", "🧪 Test Queries", "📊 System Info", "📋 Schema Editor"]
    )

    # Tab 1: PDF Processing
    with tab1:
        st.markdown(
            '<h2 class="section-header">📄 PDF Document Processing</h2>', unsafe_allow_html=True
        )

        st.markdown(
            """
        Process PDF documents from the `./data/pdfs/` directory. The system will:
        - Extract text using Mistral OCR
        - Parse structured product data
        - Store in SQLite database
        - Generate embeddings for Qdrant vector search
        """
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            limit = st.slider(
                "Number of PDFs to process",
                min_value=1,
                max_value=152,  # Total PDFs available
                value=10,
                help="Select how many PDF files to process",
            )

        with col2:
            st.metric("Available PDFs", "152")
            st.metric("Selected", limit)

        if st.button("🔄 Process PDFs", type="primary"):
            if not st.session_state.agents_initialized:
                st.error("❌ Please initialize agents first!")
            else:
                with st.spinner(f"Processing {limit} PDF files..."):
                    results = load_pdfs_batch(limit)

                if "error" not in results:
                    st.success("✅ PDF processing completed!")

                    # Display results
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Total PDFs", results["total_pdfs"])

                    with col2:
                        st.metric("Successful", results["successful"])

                    with col3:
                        st.metric("Failed", results["failed"])

                    # Show failed files if any
                    if results["failed"] > 0:
                        st.markdown("### ❌ Failed Files")
                        for detail in results["details"]:
                            if "error" in detail:
                                st.error(f"**{detail['pdf']}:** {detail['error']}")
                else:
                    st.error(f"❌ Processing failed: {results['error']}")

    # Tab 2: Search
    with tab2:
        st.markdown('<h2 class="section-header">🔍 Document Search</h2>', unsafe_allow_html=True)

        st.markdown(
            """
        Search through processed PDF documents using natural language queries.
        Supports multiple languages: German, English, French, Spanish.
        """
        )

        # Search input
        query = st.text_area(
            "Enter your search query:",
            placeholder="e.g., Was ist die Farbtemperatur von SIRIUS HRI 330W?",
            height=100,
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("🔍 Search", type="primary", disabled=not query.strip()):
                if not st.session_state.agents_initialized:
                    st.error("❌ Please initialize agents first!")
                elif not query.strip():
                    st.error("❌ Please enter a search query!")
                else:
                    with st.spinner("Searching..."):
                        results = search_query(query)

                    st.session_state.last_search_results = results
                    display_search_results(results)

        with col2:
            if st.button("🔄 Clear Results"):
                st.session_state.last_search_results = None
                st.rerun()

        # Display last search results if available
        if st.session_state.last_search_results:
            st.markdown("---")
            display_search_results(st.session_state.last_search_results)

    # Tab 3: Test Queries
    with tab3:
        st.markdown('<h2 class="section-header">🧪 Test Queries</h2>', unsafe_allow_html=True)

        st.markdown(
            """
        Run predefined test queries to validate system functionality.
        These queries test different search strategies and multilingual support.
        """
        )

        # Predefined test queries
        test_queries = [
            {
                "name": "Exact Match (German)",
                "query": "Was ist die Farbtemperatur von SIRIUS HRI 330W 2/CS 1/SKU?",
                "description": "Tests exact product specification lookup",
            },
            {
                "name": "Semantic Search (German)",
                "query": "Welche Leuchten sind gut für die Ausstattung im Operationssaal geeignet?",
                "description": "Tests semantic understanding and recommendations",
            },
            {
                "name": "Attribute Filter (German)",
                "query": "Gebe mir alle Leuchtmittel mit mindestens 1000 wattage und Lebensdauer von mehr als 400 Stunden.",
                "description": "Tests filtering by technical specifications",
            },
            {
                "name": "Product Number Lookup (German)",
                "query": "Welche Leuchte hat die primäre Erzeugnisnummer 4062172212311?",
                "description": "Tests product identification by part number",
            },
            {
                "name": "English Query",
                "query": "What is the color temperature of SIRIUS HRI 330W?",
                "description": "Tests English language support",
            },
            {
                "name": "French Query",
                "query": "Quelle est la température de couleur de SIRIUS HRI 330W?",
                "description": "Tests French language support",
            },
        ]

        # Display test queries
        for i, test_query in enumerate(test_queries):
            with st.expander(f"🧪 {test_query['name']}"):
                st.write(f"**Description:** {test_query['description']}")
                st.write(f"**Query:** {test_query['query']}")

                if st.button(f"Run Test {i+1}", key=f"test_{i}"):
                    if not st.session_state.agents_initialized:
                        st.error("❌ Please initialize agents first!")
                    else:
                        with st.spinner(f"Running test: {test_query['name']}..."):
                            results = search_query(test_query["query"])

                        display_search_results(results)

    # Tab 4: System Info
    with tab4:
        st.markdown('<h2 class="section-header">📊 System Information</h2>', unsafe_allow_html=True)

        # System configuration
        st.markdown("### ⚙️ Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Database Paths:**")
            st.write(f"• SQLite: `{settings.sqlite_path}`")
            st.write(f"• Qdrant: `{settings.qdrant_path}`")
            st.write(f"• PDF Directory: `{settings.pdf_directory}`")

        with col2:
            st.markdown("**Model Configuration:**")

            # Get actual model information
            model_info = get_actual_model_info()
            model_status = get_model_status()

            # Display each model with status
            for model_type, info in model_info.items():
                status_icon = model_status.get(model_type, "❓")
                st.write(f"• **{model_type.upper()}**: {status_icon}")
                st.write(f"  - Model: `{info['actual']}`")
                st.write(f"  - Provider: {info.get('provider', 'Unknown')}")
                if model_type == "embedding" and "dimension" in info:
                    st.write(f"  - Dimension: {info['dimension']}")
                st.write(f"  - Description: {info['description']}")
                st.write("")

        # Model capabilities
        st.markdown("### 🧠 Model Capabilities")

        model_capabilities = get_model_capabilities()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Supported Languages:**")
            for lang in model_capabilities["languages_supported"]:
                st.write(f"• {lang}")

            st.markdown("**PDF Formats:**")
            for fmt in model_capabilities["pdf_formats"]:
                st.write(f"• {fmt}")

        with col2:
            st.markdown("**Search Types:**")
            for search_type in model_capabilities["search_types"]:
                st.write(f"• {search_type}")

            st.markdown("**Performance:**")
            perf = model_capabilities["performance"]
            st.write(f"• Embedding Dimension: {perf['embedding_dimension']}")
            st.write(f"• Rerank Top-K: {perf['rerank_top_k']}")
            st.write(f"• Final Top-K: {perf['final_top_k']}")

        # System capabilities
        st.markdown("### 🚀 System Capabilities")

        capabilities = [
            "✅ Multi-agent RAG pipeline",
            "✅ Mistral OCR integration",
            "✅ Hybrid SQLite + Qdrant storage",
            "✅ Multilingual support (DE, EN, FR, ES)",
            "✅ Query classification and routing",
            "✅ Semantic and exact search",
            "✅ Result reranking",
            "✅ Fact-checking and validation",
            "✅ Citation generation",
            "✅ Confidence scoring",
        ]

        for capability in capabilities:
            st.write(capability)

        # File statistics
        st.markdown("### 📁 File Statistics")

        try:
            pdf_count = len(list(Path("./data/pdfs").glob("*.pdf")))
            st.metric("Available PDF Files", pdf_count)
        except:
            st.metric("Available PDF Files", "Unknown")

        # Database status
        st.markdown("### 🗄️ Database Status")

        try:
            from src.utils.db_manager import DatabaseManager

            db_manager = DatabaseManager(settings.sqlite_path)
            stats = db_manager.get_stats()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Products in DB", stats.get("total_products", 0))

            with col2:
                st.metric("PDFs Processed", stats.get("total_pdfs", 0))

            with col3:
                st.metric("Database Size", f"{stats.get('db_size_mb', 0):.1f} MB")

        except Exception as e:
            st.error(f"❌ Could not retrieve database stats: {e}")

        # Quick actions
        st.markdown("### 🎯 Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Initialize Databases"):
                try:
                    from scripts.init_db import main as init_db_main

                    init_db_main()
                    st.success("✅ Databases initialized!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        with col2:
            if st.button("🧪 Run All Tests"):
                try:
                    from scripts.run_tests import main as run_tests_main

                    run_tests_main()
                    st.success("✅ All tests completed!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        with col3:
            if st.button("📊 Refresh Stats"):
                st.rerun()

    # Tab 5: Schema Editor
    with tab5:
        st.markdown('<h2 class="section-header">📋 Product Schema Configuration</h2>', unsafe_allow_html=True)

        st.markdown("""
        This tab shows the current database schema defined in `src/schemas/product_schema.py`.
        The schema is automatically used for:
        - **SQL Database**: Column types and constraints
        - **LLM Parser**: Extraction targets and field descriptions
        - **Qdrant Metadata**: Fields stored with vectors for filtering

        To modify the schema, edit `src/schemas/product_schema.py` and restart the application.
        """)

        try:
            from src.schemas.product_schema import ProductSpecification
            from src.utils.schema_utils import SchemaIntrospector, format_schema_for_display

            # Get current schema
            schema_info = SchemaIntrospector.get_schema_info(ProductSpecification)

            # Display schema information
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📌 Required Fields")
                st.markdown("*These fields must be present in all products*")

                for field in schema_info["required_fields"]:
                    with st.expander(f"**{field['name']}** ({field['type']})"):
                        st.markdown(f"**Description:** {field['description']}")
                        st.markdown(f"**Type:** `{field['type']}`")
                        st.markdown(f"**Required:** ✅ Yes")
                        if "default" in field and field["default"] is not None:
                            st.markdown(f"**Default:** `{field['default']}`")

            with col2:
                st.subheader("🔧 Optional Fields")
                st.markdown("*These fields are extracted if available*")

                for field in schema_info["optional_fields"]:
                    with st.expander(f"**{field['name']}** ({field['type']})"):
                        st.markdown(f"**Description:** {field['description']}")
                        st.markdown(f"**Type:** `{field['type']}`")
                        st.markdown(f"**Required:** ⚪ No")
                        if "default" in field and field["default"] is not None:
                            st.markdown(f"**Default:** `{field['default']}`")

            # SQL Schema section
            st.markdown("---")
            st.subheader("💾 SQL Database Schema")
            st.markdown("*Automatically generated column types for SQLite*")

            sql_schema_data = []
            for field_name, sql_type in schema_info["sql_schema"].items():
                sql_schema_data.append({
                    "Field": field_name,
                    "SQL Type": sql_type,
                })

            st.dataframe(sql_schema_data, use_container_width=True, hide_index=True)

            # Qdrant metadata fields
            st.markdown("---")
            st.subheader("🔍 Qdrant Vector Metadata")
            st.markdown("*Fields stored with vectors for filtering and search*")

            metadata_fields = SchemaIntrospector.get_qdrant_metadata_fields(ProductSpecification)
            st.code(", ".join(metadata_fields))

            # Schema file viewer
            st.markdown("---")
            st.subheader("✏️ View Schema File")

            if st.button("📂 Show Schema Source Code", use_container_width=True):
                schema_file_path = Path(__file__).parent / "src" / "schemas" / "product_schema.py"

                if schema_file_path.exists():
                    with open(schema_file_path, "r") as f:
                        schema_content = f.read()

                    st.code(schema_content, language="python", line_numbers=True)

                    st.info("""
                    **To modify the schema:**
                    1. Edit `src/schemas/product_schema.py` in your code editor
                    2. Add, remove, or modify fields in the `ProductSpecification` class
                    3. Restart the Streamlit app to apply changes
                    4. Re-process PDFs to update existing data with the new schema
                    """)
                else:
                    st.error(f"Schema file not found: {schema_file_path}")

            # Instructions for schema modification
            with st.expander("📖 How to Modify the Schema"):
                st.markdown("""
                ### Adding a New Field

                ```python
                # In src/schemas/product_schema.py
                class ProductSpecification(BaseModel):
                    # ... existing fields ...

                    # Add your new field
                    brand: Optional[str] = Field(
                        None,
                        description="Product brand or manufacturer"
                    )
                ```

                ### Field Type Options

                | Python Type | SQL Type | LLM Type | Example |
                |-------------|----------|----------|---------|
                | `str` | TEXT | string | `"SIRIUS HRI 420 W"` |
                | `int` | INTEGER | integer | `420` |
                | `float` | REAL | number | `3.14` |
                | `bool` | INTEGER | boolean | `True` |
                | `List[str]` | TEXT | array of strings | `["CE", "UL"]` |
                | `Optional[type]` | type | (optional) | - |

                ### Example: Adding a "Brand" Field

                ```python
                brand: Optional[str] = Field(
                    None,
                    description="Product brand or manufacturer"
                )
                ```

                ### After Modifying:

                1. **Restart the app** to load the new schema
                2. **Re-process PDFs** to extract the new field:
                   ```bash
                   python reprocess_pdfs.py
                   ```
                3. The LLM parser will automatically try to extract it
                4. The database will automatically add the column
                """)

            # Export schema documentation
            st.markdown("---")
            if st.button("📄 Download Schema Documentation", use_container_width=True):
                schema_doc = format_schema_for_display(schema_info)
                st.download_button(
                    label="💾 Save Documentation as TXT",
                    data=schema_doc,
                    file_name="product_schema_documentation.txt",
                    mime="text/plain",
                )

        except Exception as e:
            st.error(f"❌ Error loading schema: {e}")
            st.exception(e)


if __name__ == "__main__":
    main()
