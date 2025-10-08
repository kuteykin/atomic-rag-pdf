# src/agents/data_loader_agent.py

from src.lib.base_agent import BaseAgent, BaseAgentConfig
from src.lib.system_prompt_generator import SystemPromptGenerator
from pydantic import Field


class DataLoaderAgentConfig(BaseAgentConfig):
    """Configuration for Data Loader Agent"""

    pdf_directory: str = Field(default="./data/pdfs")
    sqlite_path: str = Field(default="./storage/products.db")
    qdrant_path: str = Field(default="./storage/qdrant_storage")


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

        # System prompt
        system_prompt = SystemPromptGenerator(
            background=[
                "You are a specialized data loading agent for product documentation.",
                "Your task is to process PDF documents containing product specifications.",
                "Extract structured data and store it in both relational and vector databases.",
            ],
            steps=[
                "1. Read PDF file using OCR tool",
                "2. Parse extracted text to identify product specifications",
                "3. Store structured data in SQLite database",
                "4. Generate embeddings for text chunks",
                "5. Store embeddings in Qdrant vector database",
                "6. Ensure data consistency between both databases",
            ],
            output_instructions=[
                "Report the number of products processed",
                "Report any errors encountered",
                "Provide summary statistics of stored data",
            ],
        )

        super().__init__(config=config, system_prompt_generator=system_prompt)

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a single PDF file"""

        # Step 1: OCR extraction
        self.memory.add_message("user", f"Extract text from: {pdf_path}")
        ocr_result = self.ocr_tool.run(pdf_path)

        # Step 2: Parse structured data
        self.memory.add_message("assistant", f"OCR completed. Parsing structure...")
        parsed_products = self.parser_tool.run(ocr_result.text)

        # Step 3: Store in SQLite
        sqlite_ids = []
        for product in parsed_products:
            product_id = self.sqlite_tool.insert_product(product)
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

    def process_directory(self, directory: str = None) -> dict:
        """Process all PDFs in directory"""
        import os
        from pathlib import Path

        dir_path = directory or self.config.pdf_directory
        pdf_files = list(Path(dir_path).glob("*.pdf"))

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
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
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
