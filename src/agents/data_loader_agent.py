# src/agents/data_loader_agent.py

from src.lib.base_agent import BaseAgent, BaseAgentConfig
from pydantic import Field
from src.config.constants import (
    DEFAULT_PDF_DIRECTORY,
    DEFAULT_SQLITE_PATH,
    DEFAULT_QDRANT_PATH,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)


class DataLoaderAgentConfig(BaseAgentConfig):
    """Configuration for Data Loader Agent"""

    pdf_directory: str = Field(default=DEFAULT_PDF_DIRECTORY)
    sqlite_path: str = Field(default=DEFAULT_SQLITE_PATH)
    qdrant_path: str = Field(default=DEFAULT_QDRANT_PATH)


class DataLoaderAgent(BaseAgent):
    """
    Agent responsible for:
    1. Reading PDFs from directory
    2. Extracting text via Mistral OCR
    3. Parsing structured product data
    4. Storing in SQLite + Qdrant
    """

    def __init__(self, config: DataLoaderAgentConfig):
        # Tools for this agent
        from src.tools.ocr_tools import MistralOCRTool, MistralOCRToolConfig
        from src.tools.parser_tools import (
            StructuredParserTool,
            StructuredParserToolConfig,
        )
        from src.tools.storage_tools import (
            SQLiteStorageTool,
            QdrantStorageTool,
            EmbeddingTool,
        )
        from src.tools.storage_tools import (
            SQLiteStorageToolConfig,
            QdrantStorageToolConfig,
            EmbeddingToolConfig,
        )
        from src.config.settings import settings

        # Initialize tools
        self.ocr_tool = MistralOCRTool(MistralOCRToolConfig(api_key=settings.mistral_api_key))
        self.parser_tool = StructuredParserTool(StructuredParserToolConfig())
        self.sqlite_tool = SQLiteStorageTool(SQLiteStorageToolConfig(db_path=config.sqlite_path))
        self.qdrant_tool = QdrantStorageTool(
            QdrantStorageToolConfig(qdrant_path=config.qdrant_path)
        )
        self.embedding_tool = EmbeddingTool(EmbeddingToolConfig())

        # Initialize base agent
        super().__init__(config)

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a single PDF file"""

        # Step 1: OCR extraction
        print(f"📄 Extracting text from: {pdf_path}")
        ocr_result = self.ocr_tool.run(pdf_path)

        # Step 2: Parse structured data
        print(f"🔍 Parsing structured data...")
        parsed_products = self.parser_tool.run(ocr_result["text"], pdf_path)

        # Step 3: Store in SQLite (using upsert to handle duplicates)
        sqlite_ids = []
        for product in parsed_products:
            product_id = self.sqlite_tool.upsert_product(product)
            sqlite_ids.append(product_id)

        # Step 4: Generate embeddings and store in Qdrant
        qdrant_ids = []
        for i, product in enumerate(parsed_products):
            # Chunk product description
            chunks = self.chunk_text(product.full_description)

            for chunk in chunks:
                # Generate embedding
                embedding = self.embedding_tool.generate(chunk)

                # Store in Qdrant with metadata
                point_id = self.qdrant_tool.insert_point(
                    vector=embedding,
                    payload={
                        "product_id": sqlite_ids[i],
                        "text": chunk,
                        "product_name": product.product_name,
                        "sku": product.sku,
                        "watt": product.watt,
                        "lebensdauer_stunden": product.lebensdauer_stunden,
                        "source_pdf": pdf_path,
                    },
                )
                qdrant_ids.append(point_id)

        return {
            "pdf": pdf_path,
            "products_processed": len(parsed_products),
            "sqlite_ids": sqlite_ids,
            "qdrant_points": len(qdrant_ids),
        }

    def process_directory(self, directory: str = None, limit: int = None) -> dict:
        """Process PDFs in directory with optional limit"""
        import os
        from pathlib import Path

        dir_path = directory or self.config.pdf_directory
        pdf_files = list(Path(dir_path).glob("*.pdf"))

        # Apply limit if specified
        if limit is not None:
            pdf_files = pdf_files[:limit]
            print(f"📄 Processing first {len(pdf_files)} PDF files (limit: {limit})")
        else:
            print(f"📄 Processing all {len(pdf_files)} PDF files")

        results = []
        for pdf_file in pdf_files:
            try:
                result = self.process_pdf(str(pdf_file))
                results.append(result)
                print(f"✓ Processed: {pdf_file.name}")
            except Exception as e:
                print(f"✗ Error processing {pdf_file.name}: {e}")
                results.append({"pdf": str(pdf_file), "error": str(e)})

        return {
            "total_pdfs": len(pdf_files),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "details": results,
        }

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []

        words = text.split()
        chunks = []

        # If text is shorter than chunk_size, return as single chunk
        if len(words) <= chunk_size:
            return [text]

        # Ensure we don't have negative step size
        step_size = max(1, chunk_size - overlap)

        for i in range(0, len(words), step_size):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)

        return chunks

    def process(self, pdf_path: str = None, directory: str = None, **kwargs) -> dict:
        """Required by BaseAgent - processes PDF loading"""
        if directory:
            return self.process_directory(directory)
        elif pdf_path:
            return self.process_pdf(pdf_path)
        else:
            return self.process_directory()
