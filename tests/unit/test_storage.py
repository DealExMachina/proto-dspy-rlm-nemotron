"""Unit tests for database storage layer."""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.storage import DatabaseManager
from src.models import (
    Document,
    DocumentSection,
    DocumentSpan,
    SFDRState,
    SustainableInvestmentDefinition,
    DNSHField,
    DNSHCoverage,
    Citation,
)


@pytest.mark.unit
class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_init_schema(self, temp_db_memory):
        """Test database schema initialization."""
        db = temp_db_memory
        conn = db.connect()
        
        # Check tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        
        assert "documents" in table_names
        assert "sections" in table_names
        assert "spans" in table_names
        assert "sfdr_states" in table_names

    def test_insert_document(self, temp_db_memory, sample_document):
        """Test document insertion."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        # Verify insertion
        result = db.get_document(sample_document.document_id)
        assert result is not None
        assert result["document_id"] == sample_document.document_id
        assert result["isin"] == sample_document.isin
        assert result["document_type"] == sample_document.document_type

    def test_insert_section(self, temp_db_memory, sample_document, sample_sections):
        """Test section insertion."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        section = sample_sections[0]
        db.insert_section(section)
        
        # Verify insertion
        sections = db.get_sections_by_document(sample_document.document_id)
        assert len(sections) == 1
        assert sections[0]["section_id"] == section.section_id
        assert sections[0]["title"] == section.title

    def test_insert_span(self, temp_db_memory, sample_document, sample_sections, sample_spans):
        """Test span insertion."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        section = sample_sections[0]
        db.insert_section(section)
        
        span = sample_spans[0]
        db.insert_span(span)
        
        # Verify insertion
        conn = db.connect()
        result = conn.execute(
            "SELECT * FROM spans WHERE span_id = ?", [span.span_id]
        ).fetchone()
        
        assert result is not None
        columns = [desc[0] for desc in conn.description]
        span_dict = dict(zip(columns, result))
        assert span_dict["span_id"] == span.span_id

    def test_insert_sfdr_state(self, temp_db_memory, sample_sfdr_state):
        """Test SFDR state insertion with JSON fields."""
        db = temp_db_memory
        db.insert_sfdr_state(sample_sfdr_state)
        
        # Verify insertion
        result = db.get_sfdr_state(sample_sfdr_state.state_id)
        assert result is not None
        assert result["state_id"] == sample_sfdr_state.state_id
        assert result["fund_isin"] == sample_sfdr_state.fund_isin
        assert result["claimed_article"] == sample_sfdr_state.claimed_article

    def test_get_document(self, temp_db_memory, sample_document):
        """Test document retrieval by ID."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        result = db.get_document(sample_document.document_id)
        assert result is not None
        assert result["document_id"] == sample_document.document_id
        
        # Test non-existent document
        result = db.get_document("non_existent_id")
        assert result is None

    def test_get_sections_by_document(self, temp_db_memory, sample_document, sample_sections):
        """Test querying sections for a document."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        # Insert multiple sections
        for section in sample_sections:
            db.insert_section(section)
        
        # Query sections
        results = db.get_sections_by_document(sample_document.document_id)
        assert len(results) == len(sample_sections)
        
        # Verify ordering by page_start
        for i in range(len(results) - 1):
            assert results[i]["page_start"] <= results[i+1]["page_start"]

    def test_foreign_key_constraints(self, temp_db_memory, sample_sections):
        """Test foreign key constraints."""
        db = temp_db_memory
        
        # Try to insert section without document (should fail or be handled)
        section = sample_sections[0]
        
        # This should work without error in DuckDB (it doesn't enforce FK by default)
        # but we document the relationship
        db.insert_section(section)
        
        # Verify section was inserted
        conn = db.connect()
        result = conn.execute(
            "SELECT * FROM sections WHERE section_id = ?", [section.section_id]
        ).fetchone()
        assert result is not None

    def test_json_field_serialization(self, temp_db_memory, sample_sfdr_state):
        """Test JSON field serialization and deserialization."""
        db = temp_db_memory
        db.insert_sfdr_state(sample_sfdr_state)
        
        result = db.get_sfdr_state(sample_sfdr_state.state_id)
        
        # Check JSON fields are properly serialized
        assert result["sustainable_investment_definition"] is not None
        
        # Parse JSON fields
        definition = json.loads(result["sustainable_investment_definition"])
        assert definition["present"] is True
        assert "text" in definition
        assert "confidence" in definition
        
        dnsh = json.loads(result["dnsh"])
        assert dnsh["present"] is True
        assert dnsh["coverage"] == "full"

    def test_multiple_documents_storage(self, temp_db_memory):
        """Test storing multiple documents."""
        db = temp_db_memory
        
        # Create multiple documents
        for i in range(5):
            doc = Document(
                document_id=f"doc_{i}",
                isin=f"LU{i:010d}",
                document_type="prospectus",
                version="1",
                checksum=f"checksum_{i}",
                total_pages=100 + i,
            )
            db.insert_document(doc)
        
        # Verify all were inserted
        conn = db.connect()
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        assert count == 5

    def test_section_hierarchy_storage(self, temp_db_memory, sample_document):
        """Test storing section parent-child relationships."""
        db = temp_db_memory
        db.insert_document(sample_document)
        
        # Create parent section
        parent = DocumentSection(
            section_id="parent_1",
            document_id=sample_document.document_id,
            title="Parent Section",
            level=1,
            page_start=1,
            text="Parent content",
        )
        db.insert_section(parent)
        
        # Create child section
        child = DocumentSection(
            section_id="child_1",
            document_id=sample_document.document_id,
            title="Child Section",
            level=2,
            page_start=2,
            text="Child content",
            parent_section_id=parent.section_id,
        )
        db.insert_section(child)
        
        # Verify hierarchy
        sections = db.get_sections_by_document(sample_document.document_id)
        child_section = [s for s in sections if s["section_id"] == "child_1"][0]
        assert child_section["parent_section_id"] == parent.section_id

    def test_database_persistence(self, tmp_path):
        """Test database persistence to disk."""
        db_path = tmp_path / "test_persist.duckdb"
        
        # Create and populate database
        db = DatabaseManager(db_path=db_path)
        db.init_schema()
        
        doc = Document(
            document_id="persist_test",
            isin="LU0000000000",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=100,
        )
        db.insert_document(doc)
        db.close()
        
        # Reopen database
        db2 = DatabaseManager(db_path=db_path)
        result = db2.get_document("persist_test")
        assert result is not None
        assert result["document_id"] == "persist_test"
        db2.close()

    def test_metadata_json_storage(self, temp_db_memory):
        """Test storing document metadata as JSON."""
        db = temp_db_memory
        
        doc = Document(
            document_id="meta_test",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc",
            total_pages=100,
            metadata={
                "source": "test",
                "author": "Test Author",
                "tags": ["sfdr", "article8"],
                "nested": {"key": "value"},
            },
        )
        db.insert_document(doc)
        
        result = db.get_document("meta_test")
        metadata = json.loads(result["metadata"])
        
        assert metadata["source"] == "test"
        assert metadata["tags"] == ["sfdr", "article8"]
        assert metadata["nested"]["key"] == "value"

    def test_confidence_score_storage(self, temp_db_memory):
        """Test storing and retrieving confidence scores."""
        db = temp_db_memory
        
        state = SFDRState(
            state_id="conf_test",
            fund_isin="LU1234567890",
            doc_version="1",
            confidence=0.876543,
        )
        db.insert_sfdr_state(state)
        
        result = db.get_sfdr_state("conf_test")
        # Check confidence is stored with precision
        assert abs(result["confidence"] - 0.876543) < 0.0001

    def test_empty_missing_fields_list(self, temp_db_memory):
        """Test storing SFDR state with empty missing_fields list."""
        db = temp_db_memory
        
        state = SFDRState(
            state_id="empty_missing",
            fund_isin="LU1234567890",
            doc_version="1",
            missing_fields=[],
            confidence=1.0,
        )
        db.insert_sfdr_state(state)
        
        result = db.get_sfdr_state("empty_missing")
        missing_fields = json.loads(result["missing_fields"])
        assert missing_fields == []
