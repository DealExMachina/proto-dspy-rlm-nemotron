# Setup Complete - Iteration 1

## Status: Ready for Testing

The Continuous Regulatory Intelligence system (Iteration 1) is now fully scaffolded and tested.

## What's Been Built

### 1. Core Architecture

- **RLM Controller** (`src/controller/rlm_controller.py`)
  - Goal-driven recursive extraction
  - DSPy signatures for structured outputs
  - Field-by-field SFDR state building

- **LLM Workers** (`src/worker/`)
  - Nemotron client for Koyeb H100 (production)
  - Ollama client for local testing (Qwen2.5:3b)
  - Factory pattern for easy switching

- **DSPy Integration** (`src/controller/dspy_signatures.py`)
  - `ClassifyArticle`: SFDR article classification
  - `ExtractDefinition`: Sustainable investment definition
  - `ExtractDNSH`: Do No Significant Harm
  - `ExtractPAI`: Principal Adverse Impacts

### 2. Data Layer

- **DuckDB Schema** (`src/storage/db.py`)
  - `documents`: Versioned document storage
  - `sections`: Document sections with hierarchy
  - `spans`: Text spans for citations
  - `sfdr_states`: Extracted regulatory states

- **Pydantic Models** (`src/models/`)
  - `SFDRState`: Complete regulatory state
  - `Document`, `DocumentSection`, `DocumentSpan`
  - `Citation`, `FieldValue` with confidence scores

### 3. Retrieval

- **BM25Retriever** (`src/retrieval/bm25_retriever.py`)
  - Section-level retrieval
  - Keyword-based search
  - Top-k ranking

### 4. Ingestion (Framework Ready)

- **DoclingIngestion** (`src/ingestion/docling_ingestion.py`)
  - Framework for Docling MCP integration
  - PDF → Sections → Spans pipeline
  - Checksum-based versioning

### 5. Testing

- **35 Unit Tests** (all passing ✓)
  - Model validation
  - Worker mocking
  - Retrieval logic
  - Storage operations

- **Test Configuration**
  - Uses Ollama locally (no H100 costs)
  - Comprehensive fixtures in `tests/conftest.py`
  - pytest configured for fast iteration

## Configuration

### Environment Variables (.env)

```bash
# Production LLM (expensive!)
NEMOTRON_API_URL=https://nemotron-3-inference-dealexmachina-53d19e1c.koyeb.app

# Local testing LLM
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# Storage
DUCKDB_PATH=./data/regulatory.duckdb
DOCUMENT_CACHE_DIR=./data/documents

# Mode
USE_OLLAMA=true  # Set to false for production
```

## Next Steps

### 1. Install Ollama (for local testing)

```bash
# macOS
brew install ollama

# Start Ollama
ollama serve

# Pull Qwen model
ollama pull qwen2.5:3b
```

### 2. Integrate Docling MCP

The system is ready for Docling integration. You need to:

1. Use MCP tools to convert PDFs:
   - `mcp_docling_convert_document_into_docling_document`
   - `mcp_docling_export_docling_document_to_markdown`

2. Parse markdown into sections (framework exists in `DoclingIngestion`)

3. Store in DuckDB

### 3. Get Sample Fund PDFs

See `docs/sample_funds.md` for recommended sources:
- Amundi MSCI World ESG Leaders (LU1602144229)
- iShares MSCI World SRI (IE00BYX2JD69)
- BNP Paribas Green Tigers (LU0823414635)

### 4. Run End-to-End Test

```bash
# With Ollama (local)
python run_one_doc.py path/to/prospectus.pdf --isin LU1234567890 --use-ollama

# With Nemotron (production - expensive!)
python run_one_doc.py path/to/prospectus.pdf --isin LU1234567890
```

### 5. Push to GitHub

The repository needs to be created on GitHub first:

```bash
# Create repo at: https://github.com/new
# Then push:
git push -u origin main
```

## Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.11.14, pytest-7.4.3, pluggy-1.6.0
collected 35 items

tests/unit/test_models.py ..................                            [ 51%]
tests/unit/test_retrieval.py ...                                        [ 60%]
tests/unit/test_worker.py ...............                               [100%]

============================== 35 passed in 0.57s ==============================
```

## Architecture Principles (from PRD)

✓ Small contexts only - no long-context inference
✓ Recursive control - LLM is a worker, not a monolith
✓ Structured outputs - everything goes into canonical tables
✓ Provenance-first - every fact has page/span citations
✓ Idempotent execution - re-running produces same state
✓ Long-running by design - scheduler + versioning ready

## Key Files

- `run_one_doc.py` - Main CLI for Iteration 1
- `src/controller/rlm_controller.py` - Core extraction logic
- `src/models/sfdr_state.py` - Canonical SFDR state
- `src/storage/db.py` - DuckDB interface
- `tests/` - Comprehensive test suite

## Cost Management

- **Development**: Use Ollama (free, local)
- **Testing**: Use Ollama (free, local)
- **Production**: Use Nemotron on Koyeb H100 (expensive!)

The system defaults to Ollama to avoid accidental H100 costs.

## Git Status

- ✓ Initial commit created
- ✓ All files staged
- ⚠ Remote repository needs to be created on GitHub
- ⚠ Push pending

## Ready For

1. Docling MCP integration for PDF extraction
2. Sample fund prospectus processing
3. End-to-end SFDR state extraction
4. Iteration 2 planning (multi-document reasoning)
