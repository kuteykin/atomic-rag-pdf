# src/tools/ocr_tools.py

from src.lib.base_tool import BaseTool, BaseToolConfig
from pydantic import Field
from mistralai import Mistral
from src.config.constants import DEFAULT_OCR_MODEL


class MistralOCRToolConfig(BaseToolConfig):
    api_key: str = Field(..., description="Mistral API key")
    model: str = Field(
        default=DEFAULT_OCR_MODEL, description="Mistral OCR model - optimal for English PDFs"
    )


class MistralOCRTool(BaseTool):
    """Tool for extracting text from PDFs using Mistral OCR API"""

    def __init__(self, config: MistralOCRToolConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.client = Mistral(api_key=self.api_key)

    def run(self, pdf_path: str) -> dict:
        """Extract text from PDF using Mistral OCR API"""
        try:
            # Convert local file to base64 for API
            import base64

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode()

            # Use Mistral OCR API with base64 document
            ocr_response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{pdf_base64}",
                },
                include_image_base64=True,
            )

            # Extract text from response
            extracted_text = ""
            if hasattr(ocr_response, "pages") and ocr_response.pages:
                # Combine all pages' markdown content
                page_texts = []
                for page in ocr_response.pages:
                    if hasattr(page, "markdown") and page.markdown:
                        page_texts.append(page.markdown)
                extracted_text = "\n\n--- Page Separator ---\n\n".join(page_texts)

            pages_processed = len(ocr_response.pages) if hasattr(ocr_response, "pages") else 0

            return {
                "text": extracted_text,
                "pdf_path": pdf_path,
                "model_used": self.model,
                "pages_processed": pages_processed,
                "response": ocr_response,
            }

        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return {
                "text": f"Error processing PDF: {e}",
                "pdf_path": pdf_path,
                "model_used": self.model,
                "pages_processed": 0,
                "response": None,
            }
