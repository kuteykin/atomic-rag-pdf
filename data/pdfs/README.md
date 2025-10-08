# data/pdfs/README.md

# PDF Data Directory

Place your PDF files containing product specifications in this directory.

## Supported Formats
- PDF files with product catalogs
- Technical specifications
- Product datasheets

## Processing
The DataLoaderAgent will:
1. Extract text using Mistral OCR
2. Parse structured product data
3. Store in SQLite + Qdrant databases

## Example Usage
```bash
# Copy PDFs to this directory
cp /path/to/product-catalog.pdf ./data/pdfs/

# Process all PDFs
poetry run atomic-rag load --pdf-dir ./data/pdfs
```
