"""Shared pytest fixtures for all tests."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.models import (
    Document,
    DocumentSection,
    DocumentSpan,
    SFDRState,
    SustainableInvestmentDefinition,
    DNSHField,
    DNSHCoverage,
    PAIField,
    Citation,
)
from src.storage import DatabaseManager
from src.worker import LLMWorker


@pytest.fixture
def temp_db():
    """Create an in-memory DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        db = DatabaseManager(db_path=db_path)
        db.init_schema()
        yield db
        db.close()


@pytest.fixture
def temp_db_memory():
    """Create an in-memory DuckDB database (faster for unit tests)."""
    db = DatabaseManager(db_path=Path(":memory:"))
    db.init_schema()
    yield db
    db.close()


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    return Document(
        document_id="test_doc_123",
        isin="LU1234567890",
        document_type="prospectus",
        version="1",
        checksum="abc123def456",
        source_path="/path/to/test.pdf",
        total_pages=100,
        processed=True,
        metadata={"test": "data"},
    )


@pytest.fixture
def sample_sections(sample_document) -> List[DocumentSection]:
    """Create sample document sections for testing."""
    return [
        DocumentSection(
            section_id="sec_1",
            document_id=sample_document.document_id,
            title="Investment Objective",
            level=1,
            page_start=5,
            page_end=7,
            text="This fund aims to achieve sustainable investment goals while promoting environmental and social characteristics.",
        ),
        DocumentSection(
            section_id="sec_2",
            document_id=sample_document.document_id,
            title="Sustainable Investment Strategy",
            level=2,
            page_start=8,
            page_end=12,
            text="The fund defines sustainable investment as an investment in an economic activity that contributes to an environmental objective, measured by key resource efficiency indicators on the use of energy, renewable energy, raw materials, water and land.",
        ),
        DocumentSection(
            section_id="sec_3",
            document_id=sample_document.document_id,
            title="Do No Significant Harm (DNSH)",
            level=2,
            page_start=13,
            page_end=15,
            text="The fund ensures that investments do not significantly harm any environmental or social objective. This is achieved through comprehensive ESG screening and ongoing monitoring.",
        ),
        DocumentSection(
            section_id="sec_4",
            document_id=sample_document.document_id,
            title="Principal Adverse Impacts (PAI)",
            level=2,
            page_start=16,
            page_end=18,
            text="The fund considers all mandatory principal adverse impacts on sustainability factors. Coverage ratio is 100% for all mandatory indicators.",
        ),
    ]


@pytest.fixture
def sample_spans(sample_document, sample_sections) -> List[DocumentSpan]:
    """Create sample document spans for testing."""
    spans = []
    for i, section in enumerate(sample_sections):
        span = DocumentSpan(
            span_id=f"span_{i+1}",
            document_id=sample_document.document_id,
            section_id=section.section_id,
            page_number=section.page_start,
            start_char=0,
            end_char=len(section.text),
            text=section.text,
        )
        spans.append(span)
    return spans


@pytest.fixture
def sample_citations(sample_document) -> List[Citation]:
    """Create sample citations for testing."""
    return [
        Citation(
            document_id=sample_document.document_id,
            page_number=8,
            span_id="span_2",
            text_snippet="The fund defines sustainable investment as...",
        ),
        Citation(
            document_id=sample_document.document_id,
            page_number=13,
            span_id="span_3",
            text_snippet="The fund ensures that investments do not significantly harm...",
        ),
    ]


@pytest.fixture
def sample_sfdr_state(sample_document, sample_citations) -> SFDRState:
    """Create a complete SFDR state for testing."""
    definition = SustainableInvestmentDefinition(
        present=True,
        text="The fund defines sustainable investment as an investment in an economic activity that contributes to an environmental objective.",
        confidence=0.9,
        citations=[sample_citations[0]],
    )
    
    dnsh = DNSHField(
        present=True,
        coverage=DNSHCoverage.FULL,
        confidence=0.85,
        citations=[sample_citations[1]],
    )
    
    pai = PAIField(
        mandatory_coverage_ratio=1.0,
        confidence=0.95,
        citations=[],
    )
    
    return SFDRState(
        state_id="state_123",
        fund_isin="LU1234567890",
        doc_version="1",
        claimed_article="8",
        sustainable_investment_definition=definition,
        dnsh=dnsh,
        pai=pai,
        missing_fields=[],
        confidence=0.9,
        documents=[sample_document.document_id],
    )


@pytest.fixture
def mock_ollama_worker():
    """Mock Ollama worker with predefined responses."""
    mock_worker = Mock(spec=LLMWorker)
    
    # Default generate response
    mock_worker.generate.return_value = "This is a test response from the LLM."
    
    # Default JSON response for article classification
    def mock_generate_json(prompt, **kwargs):
        if "article" in prompt.lower() or "classification" in prompt.lower():
            return {
                "article": "8",
                "confidence": "0.85",
                "reasoning": "This fund promotes environmental characteristics.",
            }
        elif "definition" in prompt.lower():
            return {
                "definition_present": "true",
                "definition_text": "A sustainable investment is an investment in an economic activity that contributes to environmental or social objectives.",
                "page_number": "8",
                "confidence": "0.9",
            }
        elif "dnsh" in prompt.lower():
            return {
                "dnsh_present": "true",
                "coverage": "full",
                "page_number": "13",
                "confidence": "0.85",
            }
        elif "pai" in prompt.lower():
            return {
                "mandatory_coverage_ratio": "1.0",
                "page_number": "16",
                "confidence": "0.95",
            }
        else:
            return {"result": "unknown"}
    
    mock_worker.generate_json.side_effect = mock_generate_json
    
    return mock_worker


@pytest.fixture
def mock_retrieval_results(sample_sections) -> List[tuple]:
    """Mock retrieval results with sections and scores."""
    return [
        (
            {
                "section_id": section.section_id,
                "document_id": section.document_id,
                "title": section.title,
                "text": section.text,
                "page_start": section.page_start,
            },
            10.0 - i,  # Descending scores
        )
        for i, section in enumerate(sample_sections)
    ]


@pytest.fixture
def sample_markdown_document() -> str:
    """Sample markdown document for testing ingestion."""
    return """# Fund Prospectus

## Investment Objective

This fund aims to achieve long-term capital growth while promoting environmental and social characteristics.

## Sustainable Investment Strategy

### Definition of Sustainable Investment

The fund defines sustainable investment as an investment in an economic activity that contributes to an environmental objective, such as:

- Climate change mitigation
- Climate change adaptation  
- Sustainable use of water resources
- Transition to a circular economy
- Pollution prevention and control
- Protection of biodiversity

### Do No Significant Harm (DNSH)

The fund ensures that sustainable investments do not significantly harm any environmental or social objective. This is achieved through:

1. Comprehensive ESG screening of all investments
2. Exclusion policies for controversial activities
3. Ongoing monitoring and engagement with portfolio companies

Coverage: Full coverage of all six environmental objectives.

### Principal Adverse Impacts (PAI)

The fund considers principal adverse impacts on sustainability factors as follows:

- All 14 mandatory PAI indicators are monitored
- Coverage ratio: 100% of portfolio
- Annual reporting on PAI metrics

## Risk Factors

Standard investment risks apply. Past performance is not indicative of future results.

---
Page 100
"""


@pytest.fixture
def temp_test_file(tmp_path) -> Path:
    """Create a temporary test file."""
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("This is a test document for checksum computation.")
    return test_file


@pytest.fixture
def mock_http_response():
    """Mock HTTP response for worker tests."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Test response"}
    }
    mock_response.raise_for_status = Mock()
    return mock_response


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache between tests to avoid state leakage."""
    from src.config.settings import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
