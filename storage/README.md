# storage/README.md

# Storage Directory

This directory contains the persistent storage for the Atomic RAG System:

- `products.db` - SQLite database with structured product data
- `qdrant_storage/` - Qdrant vector database for embeddings

## Database Schema

### SQLite (products.db)
- **products** table: Structured product specifications
- Indexes on SKU, product name, wattage, lifetime, application area

### Qdrant (qdrant_storage/)
- **products** collection: Vector embeddings of product descriptions
- 384-dimensional vectors (sentence-transformers/all-MiniLM-L6-v2)
- Cosine similarity distance metric

## Initialization

Run `poetry run init-db` to initialize the databases.
