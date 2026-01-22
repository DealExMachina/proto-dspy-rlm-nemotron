# Continuous Regulatory Intelligence

A stateful regulatory control system using RLM/DSPy/Nemotron for SFDR compliance monitoring.

## Overview

This is NOT a chatbot or RAG demo. It is a **stateful regulatory control system** that:
- Processes long regulatory documents without long-context prompts
- Uses recursive control (RLM) to extract structured regulatory state
- Runs continuously to monitor drift and changes over time

## Architecture

- **RLM Controller**: Goal-driven recursive loop that fills SFDR state field by field
- **Nemotron Worker**: Small-context LLM for extraction tasks (via vLLM on Koyeb)
- **DSPy**: Program signatures and optimization
- **DuckDB**: Versioned document and state storage
- **Docling**: Document ingestion and parsing

## Current Status: Iteration 1

Building proof-of-concept for extracting structured SFDR state from a single long document.

## Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -m src.init_db
```

## Usage (Iteration 1)

```bash
# Process a single document
python run_one_doc.py path/to/prospectus.pdf

# Run tests (using local Ollama)
pytest tests/
```

## Testing

Unit tests run on **Ollama with Qwen3:8b** to avoid H100 costs during development.

Production uses **Nemotron on Koyeb** (H100).

## Project Structure

```
src/
  config/          # Configuration and settings
  models/          # Pydantic models for SFDR state
  ingestion/       # Document ingestion (Docling)
  retrieval/       # BM25 retrieval layer
  controller/      # RLM controller
  worker/          # LLM worker clients (Nemotron/Ollama)
  storage/         # DuckDB interface
tests/
  unit/            # Unit tests
  integration/     # Integration tests
data/              # Local data directory
docs/              # Documentation
```

## Key Principles

1. **Small contexts only**: No long-context inference
2. **Recursive control**: LLM is a worker, not a monolith
3. **Structured outputs**: Everything goes into canonical tables
4. **Provenance-first**: Every fact has page/span citations
5. **Idempotent execution**: Re-running produces the same state
6. **Long-running by design**: Scheduler + versioning from day one
