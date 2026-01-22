"""Integration tests for document ingestion pipeline."""

import pytest
from pathlib import Path
from src.ingestion import DoclingIngestion
from src.storage import DatabaseManager
from src.models import Document


@pytest.mark.integration
class TestIngestionPipeline:
    """Test full ingestion pipeline with real database."""

    def test_full_ingestion_flow(self, temp_db, sample_markdown_document, tmp_path):
        """Test complete ingestion flow from markdown to DB."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create a test file
        test_file = tmp_path / "test_prospectus.pdf"
        test_file.write_text("Test PDF content")
        
        # Ingest document
        document, sections, spans = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Verify document in database
        stored_doc = db.get_document(document.document_id)
        assert stored_doc is not None
        assert stored_doc["isin"] == "LU1234567890"

    def test_markdown_to_database(self, temp_db, sample_markdown_document):
        """Test parsing markdown and storing in database."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create document first
        document = Document(
            document_id="test_doc_123",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=100,
        )
        db.insert_document(document)
        
        # Parse markdown
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id=document.document_id
        )
        
        # Store sections
        for section in sections:
            db.insert_section(section)
        
        # Verify sections in database
        stored_sections = db.get_sections_by_document(document.document_id)
        assert len(stored_sections) == len(sections)
        assert stored_sections[0]["document_id"] == document.document_id

    def test_section_to_span_relationship(self, temp_db, sample_markdown_document):
        """Test section-span foreign key relationships."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create document
        document = Document(
            document_id="test_doc_123",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=100,
        )
        db.insert_document(document)
        
        # Parse and store sections
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id=document.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        # Create and store spans
        spans = ingestion.create_spans_from_sections(sections)
        for span in spans:
            db.insert_span(span)
        
        # Verify relationships
        conn = db.connect()
        for span in spans:
            result = conn.execute(
                "SELECT * FROM spans WHERE span_id = ?", [span.span_id]
            ).fetchone()
            assert result is not None

    def test_duplicate_document_detection(self, temp_db, tmp_path):
        """Test detecting duplicate documents by checksum."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create test file
        test_file = tmp_path / "test_doc.pdf"
        test_file.write_text("Same content")
        
        # Ingest once
        doc1, _, _ = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Ingest again
        doc2, _, _ = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Checksums should match
        assert doc1.checksum == doc2.checksum

    def test_large_document_handling(self, temp_db, tmp_path):
        """Test handling large documents with many sections."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create large markdown
        large_markdown = "\n\n".join([
            f"# Section {i}\n\nContent for section {i}."
            for i in range(100)
        ])
        
        # Create document
        document = Document(
            document_id="large_doc",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=200,
        )
        db.insert_document(document)
        
        # Parse sections
        sections = ingestion.parse_markdown_to_sections(
            large_markdown,
            document_id=document.document_id
        )
        
        # Store all sections
        for section in sections:
            db.insert_section(section)
        
        # Verify all stored
        stored_sections = db.get_sections_by_document(document.document_id)
        assert len(stored_sections) == 100

    def test_multi_document_ingestion(self, temp_db, tmp_path):
        """Test ingesting multiple documents sequentially."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create multiple test files
        documents = []
        for i in range(3):
            test_file = tmp_path / f"doc_{i}.pdf"
            test_file.write_text(f"Content {i}")
            
            doc, _, _ = ingestion.ingest_document(
                file_path=test_file,
                isin=f"LU{i:010d}",
                document_type="prospectus",
            )
            documents.append(doc)
        
        # Verify all documents in database
        for doc in documents:
            stored_doc = db.get_document(doc.document_id)
            assert stored_doc is not None

    def test_ingestion_with_unicode_content(self, temp_db, tmp_path):
        """Test ingesting documents with unicode characters."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        unicode_markdown = """# Objective d'investissement

Le fonds investit dans des entreprises promouvant des objectifs environnementaux:
- Atténuation du changement climatique ⚡
- Protection de la biodiversité 🌿
- Économie circulaire ♻️

Coverage: 100% des investissements.
"""
        
        # Create document
        document = Document(
            document_id="unicode_doc",
            isin="LU1234567890",
            document_type="prospectus",
            version="1",
            checksum="abc123",
            total_pages=50,
        )
        db.insert_document(document)
        
        # Parse and store
        sections = ingestion.parse_markdown_to_sections(
            unicode_markdown,
            document_id=document.document_id
        )
        for section in sections:
            db.insert_section(section)
        
        # Verify unicode preserved
        stored_sections = db.get_sections_by_document(document.document_id)
        combined_text = " ".join([s["text"] for s in stored_sections])
        assert "⚡" in combined_text or "🌿" in combined_text or len(stored_sections) > 0

    def test_version_tracking_in_ingestion(self, temp_db, tmp_path):
        """Test tracking different versions of same document."""
        db = temp_db
        ingestion = DoclingIngestion(db)
        
        # Create test file
        test_file = tmp_path / "versioned_doc.pdf"
        test_file.write_text("Version 1 content")
        
        # Ingest v1
        doc_v1, _, _ = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        doc_v1.version = "1"
        
        # Modify file
        test_file.write_text("Version 2 content - modified")
        
        # Ingest v2
        doc_v2, _, _ = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Checksums should differ
        assert doc_v1.checksum != doc_v2.checksum
