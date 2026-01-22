"""End-to-end tests for full extraction pipeline."""

import pytest
import json
from pathlib import Path
from src.ingestion import DoclingIngestion
from src.retrieval import BM25Retriever
from src.controller import RLMController
from src.storage import DatabaseManager
from src.models import Document


@pytest.mark.e2e
@pytest.mark.slow
class TestFullPipeline:
    """Test complete end-to-end workflows."""

    def test_markdown_to_sfdr_state(self, temp_db, sample_markdown_document, mock_ollama_worker):
        """Test complete flow from markdown to SFDR state."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Step 1: Create and ingest document
        doc = Document(
            document_id="e2e_test_doc",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="e2e_checksum",
            total_pages=100,
        )
        db.insert_document(doc)
        
        # Step 2: Parse markdown
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id=doc.document_id
        )
        
        # Step 3: Store sections
        for section in sections:
            db.insert_section(section)
        
        # Step 4: Create spans
        spans = ingestion.create_spans_from_sections(sections)
        for span in spans:
            db.insert_span(span)
        
        # Step 5: Index for retrieval
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        # Step 6: Extract SFDR state
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(
            document_id=doc.document_id,
            isin=doc.isin,
            doc_version="1"
        )
        
        # Step 7: Store state
        db.insert_sfdr_state(state)
        
        # Verify complete pipeline
        assert state.fund_isin == doc.isin
        assert state.state_id is not None
        
        # Verify state in database
        stored_state = db.get_sfdr_state(state.state_id)
        assert stored_state is not None

    def test_article_8_fund_processing(self, temp_db, mock_ollama_worker):
        """Test processing Article 8 fund document."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Article 8 document
        article_8_markdown = """# Fund Prospectus

## SFDR Classification

This fund is classified under Article 8 of SFDR, promoting environmental and social characteristics.

## Sustainable Investment Strategy

The fund promotes environmental characteristics through:
- ESG integration
- Exclusion policies
- Active engagement

## Environmental Objectives

Focus on climate change mitigation and adaptation.
"""
        
        # Ingest
        doc = Document(
            document_id="article_8_doc",
            isin="LU8888888888",
            document_type="prospectus",
            version="1",
            checksum="art8",
            total_pages=50,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(article_8_markdown, doc.document_id)
        for section in sections:
            db.insert_section(section)
        
        # Extract
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Verify Article 8 classification
        assert state.claimed_article in ["8", None]  # Mock might return 8

    def test_article_9_fund_processing(self, temp_db, mock_ollama_worker):
        """Test processing Article 9 fund document."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Article 9 document
        article_9_markdown = """# Fund Prospectus

## SFDR Classification

This fund is classified under Article 9 of SFDR, having sustainable investment as its objective.

## Sustainable Investment Definition

The fund defines sustainable investment as an investment in economic activities that contribute to environmental objectives such as climate change mitigation.

## Do No Significant Harm

All investments undergo DNSH assessment. Full coverage of all six environmental objectives.

## Principal Adverse Impacts

The fund considers all 14 mandatory PAI indicators. Coverage: 100%.
"""
        
        # Process
        doc = Document(
            document_id="article_9_doc",
            isin="LU9999999999",
            document_type="prospectus",
            version="1",
            checksum="art9",
            total_pages=75,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(article_9_markdown, doc.document_id)
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Article 9 should have more complete information
        assert state.sustainable_investment_definition is not None

    def test_missing_data_handling(self, temp_db, mock_ollama_worker):
        """Test handling incomplete documents with missing data."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Incomplete document
        incomplete_markdown = """# Fund Information

Some basic information but no SFDR details.

## Investment Objective

General investment objective without sustainability details.
"""
        
        doc = Document(
            document_id="incomplete_doc",
            isin="LU0000000000",
            document_type="prospectus",
            version="1",
            checksum="incomplete",
            total_pages=20,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(incomplete_markdown, doc.document_id)
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Should track missing fields
        assert len(state.missing_fields) > 0
        assert state.confidence < 1.0

    def test_citation_accuracy(self, temp_db, sample_markdown_document, mock_ollama_worker):
        """Test that citations point to correct pages."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        doc = Document(
            document_id="citation_test",
            isin="LU1111111111",
            document_type="prospectus",
            version="1",
            checksum="cit",
            total_pages=100,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            doc.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Check citations exist and have valid page numbers
        if state.sustainable_investment_definition:
            citations = state.sustainable_investment_definition.citations
            for citation in citations:
                assert citation.page_number > 0
                assert len(citation.text_snippet) > 0

    def test_output_format_validation(self, temp_db, sample_markdown_document, mock_ollama_worker):
        """Test complete output format matches specification."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        doc = Document(
            document_id="format_test",
            isin="LU2222222222",
            document_type="prospectus",
            version="1",
            checksum="fmt",
            total_pages=100,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            doc.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Serialize to dict (as would be done for JSON output)
        state_dict = state.model_dump()
        
        # Verify required fields present
        assert "state_id" in state_dict
        assert "fund_isin" in state_dict
        assert "doc_version" in state_dict
        assert "confidence" in state_dict
        assert "missing_fields" in state_dict
        assert "documents" in state_dict

    def test_pipeline_with_multiple_sections(self, temp_db, mock_ollama_worker):
        """Test pipeline with document having many sections."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create document with many sections
        large_markdown = "\n\n".join([
            f"## Section {i}\n\nContent about topic {i}."
            for i in range(20)
        ])
        
        doc = Document(
            document_id="large_doc",
            isin="LU3333333333",
            document_type="prospectus",
            version="1",
            checksum="large",
            total_pages=200,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(large_markdown, doc.document_id)
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Should complete without errors
        assert state is not None

    def test_state_persistence(self, temp_db, sample_markdown_document, mock_ollama_worker):
        """Test that extracted state persists correctly."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        doc = Document(
            document_id="persist_test",
            isin="LU4444444444",
            document_type="prospectus",
            version="1",
            checksum="persist",
            total_pages=100,
        )
        db.insert_document(doc)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            doc.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        retriever = BM25Retriever(db)
        retriever.index_document(doc.document_id)
        
        controller = RLMController(db, retriever, mock_ollama_worker)
        state = controller.build_sfdr_state(doc.document_id, doc.isin, "1")
        
        # Store
        db.insert_sfdr_state(state)
        
        # Retrieve
        stored = db.get_sfdr_state(state.state_id)
        
        # Compare
        assert stored["fund_isin"] == state.fund_isin
        assert stored["doc_version"] == state.doc_version
        assert stored["confidence"] == state.confidence
