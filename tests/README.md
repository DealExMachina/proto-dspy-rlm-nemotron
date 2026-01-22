# Test Suite

Comprehensive test suite for the Continuous Regulatory Intelligence system.

## Overview

This test suite follows best practices with three levels of testing:
- **Unit Tests**: Fast, isolated tests of individual components
- **Integration Tests**: Tests of component interactions with real database
- **E2E Tests**: Full pipeline tests from document to SFDR state

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (fast, mocked)
│   ├── test_models.py            # Pydantic model validation
│   ├── test_worker.py            # LLM worker tests
│   ├── test_storage.py           # Database operations
│   ├── test_retrieval.py         # BM25 retrieval
│   ├── test_ingestion.py         # Document parsing
│   ├── test_controller.py        # RLM controller logic
│   └── test_dspy_signatures.py   # DSPy signature definitions
├── integration/                   # Integration tests (DB + retrieval)
│   ├── test_ingestion_pipeline.py
│   ├── test_controller_integration.py
│   └── __init__.py
├── e2e/                          # End-to-end tests (full pipeline)
│   ├── test_cli.py
│   ├── test_full_pipeline.py
│   └── __init__.py
└── fixtures/                     # Test data
    ├── sample_documents/         # Sample markdown prospectuses
    │   ├── test_article_8.md
    │   ├── test_article_9.md
    │   └── test_incomplete.md
    └── expected_outputs/         # Expected SFDR states
        ├── expected_state_article_8.json
        └── expected_state_article_9.json
```

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### By Test Level

```bash
# Fast unit tests only (< 5 seconds)
pytest tests/unit -m unit

# Integration tests (requires database)
pytest tests/integration -m integration

# E2E tests (full pipeline)
pytest tests/e2e -m e2e
```

### By Component

```bash
# Test specific component
pytest tests/unit/test_models.py
pytest tests/unit/test_worker.py
pytest tests/unit/test_controller.py

# Test retrieval
pytest tests/unit/test_retrieval.py tests/integration/test_controller_integration.py -k retrieval
```

### By Marker

```bash
# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring Ollama
pytest -m "not ollama"

# Never run Nemotron tests (expensive H100)
pytest -m "not nemotron"
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto

# Run specific number of workers
pytest -n 4
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Fast unit tests with mocks
- `@pytest.mark.integration` - Integration tests with real DB
- `@pytest.mark.e2e` - End-to-end pipeline tests
- `@pytest.mark.slow` - Slow tests (LLM calls, large documents)
- `@pytest.mark.ollama` - Requires Ollama running locally
- `@pytest.mark.nemotron` - Requires Nemotron (H100, expensive - never run)

## Coverage Goals

- **Unit Tests**: 90%+ coverage of individual modules
- **Integration Tests**: Critical paths covered
- **E2E Tests**: Key user workflows covered
- **Overall**: 80%+ code coverage

### Check Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=80
```

## Test Configuration

Configuration is in `pytest.ini`:

- Test discovery patterns
- Markers definition
- Coverage settings
- Output verbosity
- Warning filters

## Fixtures

### Database Fixtures

- `temp_db`: Temporary DuckDB database on disk
- `temp_db_memory`: In-memory DuckDB (faster for unit tests)

### Sample Data

- `sample_document`: Document model instance
- `sample_sections`: List of DocumentSection instances
- `sample_spans`: List of DocumentSpan instances
- `sample_sfdr_state`: Complete SFDRState instance
- `sample_markdown_document`: Markdown text for parsing

### Mock Fixtures

- `mock_ollama_worker`: Mocked LLM worker with predefined responses
- `mock_retrieval_results`: Mock BM25 retrieval results
- `mock_http_response`: Mock HTTP response for worker tests

### File Fixtures

- `temp_test_file`: Temporary file for testing
- `sample_markdown_document`: Sample prospectus markdown

## Writing Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
def test_document_creation(sample_document):
    """Test document model creation."""
    assert sample_document.isin == "LU1234567890"
    assert sample_document.total_pages > 0
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_ingestion_pipeline(temp_db, sample_markdown_document):
    """Test full ingestion with real database."""
    db = temp_db
    # ... test implementation
```

### E2E Test Example

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
def test_full_pipeline(temp_db, mock_ollama_worker):
    """Test complete extraction pipeline."""
    # ... full pipeline test
```

## Continuous Integration

For CI/CD environments:

```bash
# Run fast tests only (no Ollama)
pytest -m "unit and not ollama"

# Run with coverage and XML output
pytest --cov=src --cov-report=xml -m "not nemotron and not ollama"

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

## Debugging Tests

### Verbose Output

```bash
# Show print statements
pytest -s

# Show detailed test info
pytest -vv

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x
```

### Debug Specific Test

```bash
# Run single test with debugging
pytest tests/unit/test_models.py::TestModels::test_citation_creation -vv -s

# Drop into debugger on failure
pytest --pdb
```

### Check Test Collection

```bash
# Show what tests would run
pytest --collect-only

# Show tests for specific marker
pytest --collect-only -m unit
```

## Test Data

Sample documents in `fixtures/sample_documents/`:

- **test_article_8.md**: Article 8 fund (promotes E/S characteristics)
  - Partial DNSH coverage (70%)
  - 71% PAI coverage
  - ISIN: LU0123456789

- **test_article_9.md**: Article 9 fund (sustainable investment objective)
  - Full DNSH coverage (100%)
  - 100% PAI coverage
  - ISIN: LU9876543210

- **test_incomplete.md**: Generic fund without SFDR disclosures
  - No SFDR classification
  - Missing sustainability data
  - ISIN: LU0000000001

Expected outputs validate structure and approximate values.

## Common Issues

### Tests Failing

1. **Import errors**: Ensure you're in the project root and dependencies are installed
2. **Database errors**: Check DuckDB is properly installed
3. **Mock failures**: Verify mock setup matches actual API

### Slow Tests

1. Use `-m "not slow"` to skip LLM-dependent tests
2. Use `pytest-xdist` for parallel execution
3. Mock LLM workers in unit tests

### Coverage Gaps

1. Check `htmlcov/index.html` for uncovered lines
2. Add unit tests for uncovered functions
3. Integration tests cover happy paths

## Best Practices

1. **Fast feedback**: Unit tests run in < 5 seconds
2. **Isolation**: Tests don't depend on external services (except marked ones)
3. **Realistic data**: Use actual document examples
4. **Clear names**: Test names describe what they test
5. **Minimal mocking**: Mock only external boundaries
6. **Cost-conscious**: Never call Nemotron in tests

## Test Maintenance

- Update fixtures when models change
- Add tests for new features
- Keep test dependencies minimal
- Review coverage reports regularly
- Remove obsolete tests

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov plugin](https://pytest-cov.readthedocs.io/)
- [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Testing best practices](https://docs.pytest.org/en/stable/goodpractices.html)
