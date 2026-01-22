"""Unit tests for Pydantic models."""

import pytest
import json
from datetime import datetime
from pydantic import ValidationError
from src.models import (
    Citation,
    FieldValue,
    SustainableInvestmentDefinition,
    DNSHField,
    DNSHCoverage,
    PAIField,
    SFDRState,
    Document,
    DocumentSection,
    DocumentSpan,
)


class TestModels:
    """Test Pydantic models."""

    def test_citation_creation(self):
        """Test Citation model."""
        citation = Citation(
            document_id="doc123",
            page_number=42,
            text_snippet="This is a test snippet",
        )
        
        assert citation.document_id == "doc123"
        assert citation.page_number == 42
        assert citation.text_snippet == "This is a test snippet"

    def test_sustainable_investment_definition(self):
        """Test SustainableInvestmentDefinition model."""
        citation = Citation(
            document_id="doc123",
            page_number=10,
            text_snippet="Sustainable investment definition...",
        )
        
        definition = SustainableInvestmentDefinition(
            present=True,
            text="A sustainable investment is...",
            confidence=0.9,
            citations=[citation],
        )
        
        assert definition.present is True
        assert definition.confidence == 0.9
        assert len(definition.citations) == 1

    def test_dnsh_field(self):
        """Test DNSHField model."""
        dnsh = DNSHField(
            present=True,
            coverage=DNSHCoverage.FULL,
            confidence=0.85,
            citations=[],
        )
        
        assert dnsh.present is True
        assert dnsh.coverage == DNSHCoverage.FULL
        assert dnsh.confidence == 0.85

    def test_pai_field(self):
        """Test PAIField model."""
        pai = PAIField(
            mandatory_coverage_ratio=0.75,
            confidence=0.8,
            citations=[],
        )
        
        assert pai.mandatory_coverage_ratio == 0.75
        assert pai.confidence == 0.8

    def test_sfdr_state_creation(self):
        """Test SFDRState model."""
        definition = SustainableInvestmentDefinition(
            present=True,
            text="Test definition",
            confidence=0.9,
            citations=[],
        )
        
        dnsh = DNSHField(
            present=True,
            coverage=DNSHCoverage.PARTIAL,
            confidence=0.85,
            citations=[],
        )
        
        state = SFDRState(
            state_id="state123",
            fund_isin="LU1234567890",
            doc_version="1",
            claimed_article="8",
            sustainable_investment_definition=definition,
            dnsh=dnsh,
            missing_fields=["pai"],
            confidence=0.87,
            documents=["doc123"],
        )
        
        assert state.fund_isin == "LU1234567890"
        assert state.claimed_article == "8"
        assert state.confidence == 0.87
        assert "pai" in state.missing_fields
        assert len(state.documents) == 1

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        field = FieldValue(value="test", confidence=0.5, citations=[])
        assert field.confidence == 0.5
        
        # Invalid confidence (out of range)
        with pytest.raises(ValidationError):
            FieldValue(value="test", confidence=1.5, citations=[])
        
        with pytest.raises(ValidationError):
            FieldValue(value="test", confidence=-0.1, citations=[])


class TestDocumentModels:
    """Test Document-related models."""

    def test_document_creation(self):
        """Test Document model creation with valid data."""
        doc = Document(
            document_id="doc_123",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            source_path="/path/to/doc.pdf",
            total_pages=100,
            processed=True,
            metadata={"key": "value"},
        )
        
        assert doc.document_id == "doc_123"
        assert doc.isin == "LU1234567890"
        assert doc.document_type == "prospectus"
        assert doc.total_pages == 100
        assert doc.processed is True
        assert doc.metadata["key"] == "value"

    def test_document_validation(self):
        """Test Document model validation."""
        # Missing required fields should raise error
        with pytest.raises(ValidationError):
            Document(
                document_id="doc_123",
                # missing document_type
                version="1",
                checksum="abc",
                total_pages=100,
            )

    def test_document_serialization(self):
        """Test Document model JSON serialization."""
        doc = Document(
            document_id="doc_123",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=100,
            metadata={"test": "data"},
        )
        
        # Serialize to dict
        doc_dict = doc.model_dump()
        assert doc_dict["document_id"] == "doc_123"
        assert doc_dict["metadata"]["test"] == "data"
        
        # Serialize to JSON
        doc_json = doc.model_dump_json()
        assert isinstance(doc_json, str)
        parsed = json.loads(doc_json)
        assert parsed["document_id"] == "doc_123"

    def test_section_hierarchy(self):
        """Test DocumentSection parent-child relationships."""
        parent_section = DocumentSection(
            section_id="sec_parent",
            document_id="doc_123",
            title="Main Section",
            level=1,
            page_start=1,
            text="Parent section content",
        )
        
        child_section = DocumentSection(
            section_id="sec_child",
            document_id="doc_123",
            title="Sub Section",
            level=2,
            page_start=1,
            text="Child section content",
            parent_section_id=parent_section.section_id,
        )
        
        assert child_section.parent_section_id == parent_section.section_id
        assert child_section.level > parent_section.level

    def test_span_boundaries(self):
        """Test DocumentSpan character boundaries."""
        text = "This is a test text for span boundaries."
        span = DocumentSpan(
            span_id="span_1",
            document_id="doc_123",
            section_id="sec_1",
            page_number=1,
            start_char=0,
            end_char=len(text),
            text=text,
        )
        
        assert span.start_char == 0
        assert span.end_char == len(text)
        assert span.end_char > span.start_char
        assert len(span.text) == span.end_char - span.start_char


class TestSFDRModels:
    """Test SFDR-specific models."""

    def test_sfdr_state_missing_fields(self):
        """Test tracking of missing fields in SFDR state."""
        state = SFDRState(
            state_id="state_123",
            fund_isin="LU1234567890",
            doc_version="1",
            claimed_article="8",
            missing_fields=["pai", "dnsh"],
            confidence=0.5,
        )
        
        assert "pai" in state.missing_fields
        assert "dnsh" in state.missing_fields
        assert len(state.missing_fields) == 2

    def test_citation_with_span(self):
        """Test Citation with span information."""
        citation = Citation(
            document_id="doc_123",
            page_number=42,
            span_id="span_5",
            start_char=100,
            end_char=200,
            text_snippet="This is the cited text",
        )
        
        assert citation.span_id == "span_5"
        assert citation.start_char == 100
        assert citation.end_char == 200
        assert citation.end_char > citation.start_char

    def test_dnsh_coverage_enum(self):
        """Test DNSH coverage enum values."""
        # Test all valid enum values
        dnsh_none = DNSHField(
            present=False,
            coverage=DNSHCoverage.NONE,
            confidence=0.5,
        )
        assert dnsh_none.coverage == DNSHCoverage.NONE
        
        dnsh_partial = DNSHField(
            present=True,
            coverage=DNSHCoverage.PARTIAL,
            confidence=0.7,
        )
        assert dnsh_partial.coverage == DNSHCoverage.PARTIAL
        
        dnsh_full = DNSHField(
            present=True,
            coverage=DNSHCoverage.FULL,
            confidence=0.9,
        )
        assert dnsh_full.coverage == DNSHCoverage.FULL

    def test_pai_coverage_ratio_bounds(self):
        """Test PAI coverage ratio validation."""
        # Valid ratio
        pai = PAIField(
            mandatory_coverage_ratio=0.75,
            confidence=0.8,
        )
        assert pai.mandatory_coverage_ratio == 0.75
        
        # Boundary values
        pai_zero = PAIField(mandatory_coverage_ratio=0.0, confidence=0.5)
        assert pai_zero.mandatory_coverage_ratio == 0.0
        
        pai_one = PAIField(mandatory_coverage_ratio=1.0, confidence=0.9)
        assert pai_one.mandatory_coverage_ratio == 1.0
        
        # Invalid ratio (should raise error)
        with pytest.raises(ValidationError):
            PAIField(mandatory_coverage_ratio=1.5, confidence=0.8)

    def test_field_value_with_multiple_citations(self):
        """Test FieldValue with multiple citations."""
        citations = [
            Citation(
                document_id="doc_123",
                page_number=10,
                text_snippet="First citation",
            ),
            Citation(
                document_id="doc_123",
                page_number=15,
                text_snippet="Second citation",
            ),
            Citation(
                document_id="doc_456",
                page_number=5,
                text_snippet="Citation from another doc",
            ),
        ]
        
        field = FieldValue(
            value="Test value",
            confidence=0.85,
            citations=citations,
        )
        
        assert len(field.citations) == 3
        assert field.citations[0].page_number == 10
        assert field.citations[2].document_id == "doc_456"

    def test_sfdr_state_complete(self):
        """Test complete SFDR state with all fields populated."""
        definition = SustainableInvestmentDefinition(
            present=True,
            text="Complete definition text",
            confidence=0.9,
            citations=[
                Citation(
                    document_id="doc_123",
                    page_number=10,
                    text_snippet="Definition snippet",
                )
            ],
        )
        
        dnsh = DNSHField(
            present=True,
            coverage=DNSHCoverage.FULL,
            confidence=0.85,
            citations=[],
        )
        
        pai = PAIField(
            mandatory_coverage_ratio=1.0,
            confidence=0.95,
            citations=[],
        )
        
        state = SFDRState(
            state_id="state_complete",
            fund_isin="LU1234567890",
            doc_version="1",
            claimed_article="9",
            sustainable_investment_definition=definition,
            dnsh=dnsh,
            pai=pai,
            missing_fields=[],
            confidence=0.9,
            documents=["doc_123", "doc_456"],
        )
        
        assert state.claimed_article == "9"
        assert state.sustainable_investment_definition.present is True
        assert state.dnsh.coverage == DNSHCoverage.FULL
        assert state.pai.mandatory_coverage_ratio == 1.0
        assert len(state.missing_fields) == 0
        assert len(state.documents) == 2

    def test_sfdr_state_serialization(self):
        """Test SFDR state serialization for database storage."""
        state = SFDRState(
            state_id="state_123",
            fund_isin="LU1234567890",
            doc_version="1",
            claimed_article="8",
            confidence=0.8,
            documents=["doc_123"],
        )
        
        # Serialize to dict
        state_dict = state.model_dump()
        assert state_dict["state_id"] == "state_123"
        assert state_dict["fund_isin"] == "LU1234567890"
        
        # Serialize to JSON
        state_json = state.model_dump_json()
        parsed = json.loads(state_json)
        assert parsed["claimed_article"] == "8"
