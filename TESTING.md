# Testing Guide

Comprehensive testing documentation for the Continuous Regulatory Intelligence system.

## Test Suite Overview

The project now has a complete pytest-based test suite with **3 levels** of testing:

### Test Statistics

- **16 Python test files** created
- **100+ test cases** covering all major components
- **3 sample documents** for E2E testing
- **2 expected output fixtures** for validation

### Test Coverage

```
Unit Tests (Fast, Isolated)
├── test_models.py           - Pydantic model validation (15 tests)
├── test_worker.py           - LLM worker tests (15 tests)
├── test_storage.py          - Database operations (15 tests)
├── test_retrieval.py        - BM25 retrieval (12 tests)
├── test_ingestion.py        - Document parsing (18 tests)
├── test_controller.py       - RLM controller (17 tests)
└── test_dspy_signatures.py  - DSPy signatures (8 tests)

Integration Tests (Component Interactions)
├── test_ingestion_pipeline.py    - Full ingestion flow (8 tests)
└── test_controller_integration.py - Controller + DB + Retrieval (15 tests)

E2E Tests (Full Pipeline)
├── test_cli.py              - Command-line interface (10 tests)
└── test_full_pipeline.py    - Complete workflows (10 tests)
```

## Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all unit tests (fast)
pytest tests/unit -m unit

# Run with coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Test Execution Modes

### Development Mode

```bash
# Fast unit tests only (< 5 seconds)
pytest tests/unit

# Specific component
pytest tests/unit/test_models.py -v

# Watch mode (requires pytest-watch)
ptw tests/unit
```

### Integration Testing

```bash
# Integration tests (requires DuckDB)
pytest tests/integration -m integration

# With real retrieval
pytest tests/integration/test_controller_integration.py -v
```

### Full Suite

```bash
# All tests (unit + integration + e2e)
pytest

# Parallel execution (faster)
pytest -n auto

# Stop on first failure
pytest -x
```

### CI/CD Mode

```bash
# Fast tests for CI
pytest -m "unit and not slow" --cov=src --cov-report=xml

# Coverage threshold
pytest --cov=src --cov-fail-under=80

# All except expensive tests
pytest -m "not nemotron"
```

## Test Markers

Tests are organized with pytest markers:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast, isolated unit tests | `pytest -m unit` |
| `integration` | Component interaction tests | `pytest -m integration` |
| `e2e` | End-to-end pipeline tests | `pytest -m e2e` |
| `slow` | Slow tests (LLM calls) | `pytest -m "not slow"` |
| `ollama` | Requires Ollama running | `pytest -m "not ollama"` |
| `nemotron` | Requires Nemotron (expensive) | Never run in CI |

## Key Features

### 1. Comprehensive Fixtures

Located in `tests/conftest.py`:

- **Database fixtures**: `temp_db`, `temp_db_memory`
- **Sample data**: `sample_document`, `sample_sections`, `sample_spans`
- **Mock workers**: `mock_ollama_worker` with predefined responses
- **Test files**: `temp_test_file`, `sample_markdown_document`

### 2. Realistic Test Data

Sample documents in `tests/fixtures/sample_documents/`:

- **Article 8 fund**: Promotes E/S characteristics (71% PAI coverage)
- **Article 9 fund**: Sustainable investment objective (100% coverage)
- **Incomplete fund**: No SFDR disclosures (tests error handling)

### 3. Mock Strategy

- **Unit tests**: Mock all external dependencies (HTTP, LLM, file I/O)
- **Integration tests**: Use real DB, mock LLM (or use local Ollama)
- **E2E tests**: Full pipeline with mocked or local LLM

### 4. Coverage Tracking

```bash
# Generate HTML report
pytest --cov=src --cov-report=html

# Check specific module
pytest --cov=src.controller tests/unit/test_controller.py

# See missing lines
pytest --cov=src --cov-report=term-missing
```

## Test Organization

### Unit Tests (`tests/unit/`)

Fast, isolated tests with mocked dependencies:

- **Models**: Pydantic validation, serialization, edge cases
- **Workers**: HTTP clients, error handling, response parsing
- **Storage**: Database operations, queries, transactions
- **Retrieval**: BM25 indexing, scoring, relevance
- **Ingestion**: Markdown parsing, section extraction
- **Controller**: Extraction logic, confidence calculation
- **DSPy**: Signature definitions and field validation

### Integration Tests (`tests/integration/`)

Component interaction tests with real database:

- **Ingestion Pipeline**: Markdown → DB with sections/spans
- **Controller Integration**: Retrieval + Extraction + Storage
- **Retrieval Integration**: BM25 with real database queries

### E2E Tests (`tests/e2e/`)

Full pipeline tests simulating user workflows:

- **CLI Tests**: Command-line interface validation
- **Full Pipeline**: Document → SFDR state extraction
- **Article 8/9**: Fund-specific processing
- **Error Handling**: Missing data scenarios

## Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import Mock

@pytest.mark.unit
def test_feature(sample_fixture):
    """Test specific feature behavior."""
    # Arrange
    component = MyComponent()
    
    # Act
    result = component.do_something()
    
    # Assert
    assert result.is_valid()
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
def test_integration(temp_db, mock_ollama_worker):
    """Test component integration."""
    # Setup components
    db = temp_db
    component = MyComponent(db)
    
    # Execute integration
    result = component.process()
    
    # Verify database state
    stored = db.get_result(result.id)
    assert stored is not None
```

### E2E Test Template

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
def test_end_to_end(temp_db, sample_markdown_document, mock_ollama_worker):
    """Test complete workflow."""
    # Full pipeline execution
    state = run_full_pipeline(sample_markdown_document)
    
    # Validate output
    assert state.confidence > 0.8
    assert len(state.missing_fields) == 0
```

## Debugging Tests

### Show Output

```bash
# See print statements
pytest -s

# Verbose output
pytest -vv

# Show local variables on failure
pytest -l
```

### Run Specific Test

```bash
# Single test
pytest tests/unit/test_models.py::TestModels::test_citation_creation

# Test class
pytest tests/unit/test_models.py::TestModels

# Match pattern
pytest -k "citation"
```

### Debug on Failure

```bash
# Drop into pdb on failure
pytest --pdb

# Stop on first failure and debug
pytest -x --pdb
```

## Continuous Integration

Recommended CI configuration:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit -m unit --cov=src --cov-report=xml
      
      - name: Check coverage
        run: |
          pytest --cov=src --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

1. **Fast Feedback**: Unit tests complete in < 5 seconds
2. **Isolation**: Tests don't depend on external services
3. **Realistic Data**: Use actual document examples
4. **Clear Names**: Test names describe behavior
5. **Minimal Mocking**: Mock only boundaries
6. **Cost-Conscious**: Never call expensive APIs in tests

## Coverage Goals

- **Unit Tests**: 90%+ module coverage
- **Integration Tests**: Critical paths
- **E2E Tests**: Key workflows
- **Overall**: 80%+ code coverage

Current test counts:
- Unit tests: ~100 tests
- Integration tests: ~23 tests
- E2E tests: ~20 tests
- **Total: ~143 test cases**

## Common Issues

### Import Errors

```bash
# Ensure you're in project root
cd /path/to/proto-continuous-monitoring

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Errors

```bash
# Verify DuckDB installed
pip install duckdb

# Check permissions
ls -la data/
```

### Mock Failures

Ensure mocks match actual API:

```python
# Check actual API response format
mock_response.json.return_value = {
    "message": {"content": "text"}  # Ollama format
}
```

## Resources

- Test suite: `tests/README.md`
- Fixtures: `tests/fixtures/README.md`
- pytest docs: https://docs.pytest.org/
- Coverage: https://pytest-cov.readthedocs.io/

## Next Steps

1. Run tests: `pytest tests/unit`
2. Check coverage: `pytest --cov=src --cov-report=html`
3. Add tests for new features
4. Set up CI/CD pipeline
5. Monitor coverage over time
