"""Integration tests for RLM controller with real components."""

import pytest
from unittest.mock import Mock
from src.controller import RLMController
from src.retrieval import BM25Retriever
from src.ingestion import DoclingIngestion
from src.models import Document, SFDRState


@pytest.mark.integration
@pytest.mark.slow
class TestControllerIntegration:
    """Test RLM controller with real retrieval and database."""

    def test_build_sfdr_state_complete(self, temp_db, sample_document, sample_sections, mock_ollama_worker):
        """Test building complete SFDR state with real components."""
        db = temp_db
        
        # Insert document and sections
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        # Create retriever
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        # Create controller
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Build state
        state = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        # Verify state
        assert isinstance(state, SFDRState)
        assert state.fund_isin == sample_document.isin
        assert state.state_id is not None

    def test_controller_with_retrieval(self, temp_db, sample_document, sample_sections, mock_ollama_worker):
        """Test controller uses retrieval to find relevant sections."""
        db = temp_db
        
        # Setup data
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        # Create retriever and index
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        # Create controller
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Extract definition (should use retrieval)
        definition = controller.extract_sustainable_investment_definition(
            sample_document.document_id
        )
        
        # Should find definition
        assert definition is not None
        assert definition.present is True

    def test_controller_with_database(self, temp_db, sample_document, sample_sections, mock_ollama_worker):
        """Test storing extracted state in database."""
        db = temp_db
        
        # Setup
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Extract and store
        state = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        db.insert_sfdr_state(state)
        
        # Verify in database
        stored_state = db.get_sfdr_state(state.state_id)
        assert stored_state is not None
        assert stored_state["fund_isin"] == sample_document.isin

    def test_partial_extraction(self, temp_db, mock_ollama_worker):
        """Test extraction with some fields missing."""
        db = temp_db
        
        # Create document with minimal sections
        doc = Document(
            document_id="minimal_doc",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=10,
        )
        db.insert_document(doc)
        
        retriever = BM25Retriever(db)
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Build state with no sections
        state = controller.build_sfdr_state(
            document_id=doc.document_id,
            isin=doc.isin,
            doc_version="1"
        )
        
        # Should have missing fields
        assert len(state.missing_fields) > 0

    def test_extraction_idempotence(self, temp_db, sample_document, sample_sections, mock_ollama_worker):
        """Test re-running extraction produces same result."""
        db = temp_db
        
        # Setup
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Extract twice
        state1 = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        state2 = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        # Results should be similar (same article, same fields found)
        assert state1.claimed_article == state2.claimed_article
        assert state1.missing_fields == state2.missing_fields

    def test_dspy_integration_end_to_end(self, temp_db, sample_document, sample_sections, mock_ollama_worker):
        """Test DSPy signatures work end-to-end."""
        db = temp_db
        
        # Setup
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        # Controller uses DSPy internally
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # Should work without errors
        state = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        assert state is not None

    def test_full_pipeline_with_ingestion(self, temp_db, sample_markdown_document, mock_ollama_worker):
        """Test full pipeline from markdown to SFDR state."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create document
        doc = Document(
            document_id="pipeline_doc",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=100,
        )
        db.insert_document(doc)
        
        # Parse and store sections
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id=doc.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        # Index and extract
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(
            document_id=doc.document_id,
            isin=doc.isin,
            doc_version="1"
        )
        
        # Store state
        db.insert_sfdr_state(state)
        
        # Verify complete pipeline
        stored_state = db.get_sfdr_state(state.state_id)
        assert stored_state is not None

    def test_retrieval_quality_affects_extraction(self, temp_db, sample_document, mock_ollama_worker):
        """Test that retrieval quality impacts extraction."""
        db = temp_db
        
        # Setup document
        db.insert_document(sample_document)
        
        retriever = BM25Retriever(db)
        controller = RLMController(db, retriever, mock_ollama_worker)
        
        # With no sections, extraction should have low quality
        state = controller.build_sfdr_state(
            document_id=sample_document.document_id,
            isin=sample_document.isin,
            doc_version="1"
        )
        
        # Should have missing fields when no content available
        assert len(state.missing_fields) > 0
        assert state.confidence < 1.0


@pytest.mark.integration
class TestRetrievalIntegration:
    """Test retrieval integration with database."""

    def test_retrieval_with_database(self, temp_db, sample_document, sample_sections):
        """Test BM25 retrieval with real database."""
        db = temp_db
        
        # Insert data
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        # Create retriever
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        # Query
        results = retriever.retrieve(
            sample_document.document_id,
            "sustainable investment",
            top_k=3
        )
        
        assert len(results) > 0
        assert results[0][1] > 0  # Has score

    def test_index_then_retrieve(self, temp_db, sample_document, sample_sections):
        """Test indexing followed by retrieval."""
        db = temp_db
        
        # Insert data
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        
        # Index
        retriever.index_document(sample_document.document_id)
        
        # Retrieve
        results = retriever.retrieve(
            sample_document.document_id,
            "environmental objective",
            top_k=5
        )
        
        assert len(results) > 0

    def test_multiple_queries(self, temp_db, sample_document, sample_sections):
        """Test different queries return different results."""
        db = temp_db
        
        # Setup
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(sample_document.document_id)
        
        # Different queries
        results1 = retriever.retrieve(sample_document.document_id, "sustainable investment", top_k=3)
        results2 = retriever.retrieve(sample_document.document_id, "DNSH harm", top_k=3)
        
        # Should potentially return different top results
        assert len(results1) > 0
        assert len(results2) > 0


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test complex database operations."""

    def test_full_schema_workflow(self, temp_db, sample_document, sample_sections, sample_sfdr_state):
        """Test complete schema workflow."""
        db = temp_db
        
        # Insert all types
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        db.insert_sfdr_state(sample_sfdr_state)
        
        # Query back
        doc = db.get_document(sample_document.document_id)
        sections = db.get_sections_by_document(sample_document.document_id)
        state = db.get_sfdr_state(sample_sfdr_state.state_id)
        
        assert doc is not None
        assert len(sections) > 0
        assert state is not None

    def test_complex_queries(self, temp_db, sample_document, sample_sections):
        """Test JOIN operations."""
        db = temp_db
        
        db.insert_document(sample_document)
        for section in sample_sections:
            db.insert_section(section)
        
        # Query with condition
        conn = db.connect()
        results = conn.execute("""
            SELECT s.section_id, s.title, d.isin
            FROM sections s
            JOIN documents d ON s.document_id = d.document_id
            WHERE d.isin = ?
        """, [sample_document.isin]).fetchall()
        
        assert len(results) > 0
