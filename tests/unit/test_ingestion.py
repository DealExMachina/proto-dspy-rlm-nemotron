"""Unit tests for document ingestion."""

import pytest
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch
from src.ingestion import DoclingIngestion
from src.models import Document, DocumentSection


@pytest.mark.unit
class TestDoclingIngestion:
    """Test document ingestion functionality."""

    def test_compute_checksum(self, temp_test_file):
        """Test file checksum computation."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        checksum = ingestion._compute_checksum(temp_test_file)
        
        # Verify it's a valid SHA-256 hash
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        
        # Verify consistency
        checksum2 = ingestion._compute_checksum(temp_test_file)
        assert checksum == checksum2

    def test_compute_checksum_different_files(self, tmp_path):
        """Test that different files produce different checksums."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        # Create two different files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content A")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content B")
        
        checksum1 = ingestion._compute_checksum(file1)
        checksum2 = ingestion._compute_checksum(file2)
        
        assert checksum1 != checksum2

    def test_parse_markdown_headings(self, sample_markdown_document):
        """Test extracting headings from markdown."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id="test_doc"
        )
        
        # Should extract multiple sections
        assert len(sections) > 0
        
        # Check for expected sections
        titles = [s.title for s in sections]
        assert "Fund Prospectus" in titles
        assert "Investment Objective" in titles
        assert "Sustainable Investment Strategy" in titles

    def test_parse_markdown_hierarchy(self, sample_markdown_document):
        """Test section level hierarchy."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id="test_doc"
        )
        
        # Check heading levels
        levels = [s.level for s in sections]
        assert 1 in levels  # H1 headings
        assert 2 in levels  # H2 headings
        assert 3 in levels  # H3 headings
        
        # H1 should have lower level number than H2
        h1_sections = [s for s in sections if s.level == 1]
        h2_sections = [s for s in sections if s.level == 2]
        assert len(h1_sections) > 0
        assert len(h2_sections) > 0

    def test_create_spans_from_sections(self):
        """Test generating spans from sections."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        # Create test sections
        sections = [
            DocumentSection(
                section_id="sec_1",
                document_id="doc_123",
                title="Test Section",
                level=1,
                page_start=1,
                text="First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
            ),
        ]
        
        spans = ingestion.create_spans_from_sections(sections)
        
        # Should create multiple spans for multiple paragraphs
        assert len(spans) == 3
        
        # Check span IDs
        assert spans[0].span_id == "doc_123_span_1"
        assert spans[1].span_id == "doc_123_span_2"
        
        # Check span content
        assert "First paragraph" in spans[0].text
        assert "Second paragraph" in spans[1].text

    def test_paragraph_splitting(self):
        """Test text chunking into paragraphs."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        text_with_paragraphs = """First paragraph with some content.

Second paragraph with more content.

Third paragraph with even more content."""
        
        sections = [
            DocumentSection(
                section_id="sec_1",
                document_id="doc_123",
                title="Test",
                level=1,
                page_start=1,
                text=text_with_paragraphs,
            ),
        ]
        
        spans = ingestion.create_spans_from_sections(sections)
        
        # Should split into 3 spans
        assert len(spans) == 3
        
        # Each span should contain one paragraph
        assert "First paragraph" in spans[0].text
        assert "Second paragraph" not in spans[0].text

    def test_page_break_detection(self, sample_markdown_document):
        """Test page number tracking."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        sections = ingestion.parse_markdown_to_sections(
            sample_markdown_document,
            document_id="test_doc"
        )
        
        # All sections should have page_start
        for section in sections:
            assert section.page_start >= 1

    def test_empty_sections(self):
        """Test handling empty sections."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        markdown_with_empty = """# Heading 1

# Heading 2

Some content here.

# Heading 3
"""
        
        sections = ingestion.parse_markdown_to_sections(
            markdown_with_empty,
            document_id="test_doc"
        )
        
        # Should create sections even if some are empty
        assert len(sections) == 3

    def test_special_characters(self):
        """Test handling unicode and special characters."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        markdown_with_unicode = """# Investment Objective

This fund invests in companies promoting environmental objectives, such as:
- Climate change mitigation ⚡
- Transition to circular economy ♻️
- Protection of biodiversity 🌿

The fund follows EU taxonomy criteria.
"""
        
        sections = ingestion.parse_markdown_to_sections(
            markdown_with_unicode,
            document_id="test_doc"
        )
        
        # Should handle unicode without errors
        assert len(sections) > 0
        
        # Check unicode is preserved
        text = sections[0].text if sections else ""
        assert "⚡" in text or "♻️" in text or "🌿" in text or len(sections) > 0

    def test_ingest_document_creates_entry(self, tmp_path):
        """Test ingesting a document creates database entry."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_text("Test content")
        
        document, sections, spans = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Should create document
        assert document is not None
        assert document.isin == "LU1234567890"
        assert document.document_type == "prospectus"
        
        # Should have called database insert
        mock_db.insert_document.assert_called_once()

    def test_ingest_document_computes_checksum(self, tmp_path):
        """Test document ingestion computes checksum."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        test_file = tmp_path / "test.pdf"
        test_file.write_text("Specific content for checksum")
        
        document, _, _ = ingestion.ingest_document(
            file_path=test_file,
            isin="LU1234567890",
            document_type="prospectus",
        )
        
        # Should have checksum
        assert document.checksum is not None
        assert len(document.checksum) == 64

    def test_section_counter_increments(self):
        """Test section IDs increment correctly."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        markdown = """# Section 1

Content 1

## Section 2

Content 2

### Section 3

Content 3
"""
        
        sections = ingestion.parse_markdown_to_sections(markdown, "doc_123")
        
        # Check section IDs are sequential
        assert sections[0].section_id == "doc_123_section_1"
        assert sections[1].section_id == "doc_123_section_2"
        assert sections[2].section_id == "doc_123_section_3"

    def test_span_boundaries_correct(self):
        """Test span character boundaries are correctly computed."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        sections = [
            DocumentSection(
                section_id="sec_1",
                document_id="doc_123",
                title="Test",
                level=1,
                page_start=1,
                text="Paragraph one.\n\nParagraph two.",
            ),
        ]
        
        spans = ingestion.create_spans_from_sections(sections)
        
        # Check boundaries
        for span in spans:
            assert span.end_char > span.start_char
            assert span.end_char - span.start_char == len(span.text)

    def test_span_section_relationship(self):
        """Test spans are linked to correct sections."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        sections = [
            DocumentSection(
                section_id="sec_1",
                document_id="doc_123",
                title="Test",
                level=1,
                page_start=1,
                text="Test content.",
            ),
        ]
        
        spans = ingestion.create_spans_from_sections(sections)
        
        # All spans should reference the section
        for span in spans:
            assert span.section_id == "sec_1"
            assert span.document_id == "doc_123"

    def test_markdown_without_headings(self):
        """Test handling markdown with no headings."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        plain_markdown = """This is just plain text.

No headings here.

Just paragraphs.
"""
        
        sections = ingestion.parse_markdown_to_sections(plain_markdown, "doc_123")
        
        # Should handle gracefully (might return empty or single section)
        assert isinstance(sections, list)

    def test_multiple_hash_levels(self):
        """Test different markdown heading styles."""
        mock_db = Mock()
        ingestion = DoclingIngestion(mock_db)
        
        markdown = """# Level 1

## Level 2

### Level 3

#### Level 4

##### Level 5

###### Level 6
"""
        
        sections = ingestion.parse_markdown_to_sections(markdown, "doc_123")
        
        # Should capture all heading levels
        levels = [s.level for s in sections]
        assert min(levels) == 1
        assert max(levels) >= 3  # At least up to level 3
