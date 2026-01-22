"""Unit tests for retrieval layer."""

import pytest
from unittest.mock import Mock
from src.retrieval import BM25Retriever


class TestBM25Retriever:
    """Test BM25 retrieval."""

    def test_retrieve_empty_document(self):
        """Test retrieval with no sections."""
        mock_db = Mock()
        mock_db.get_sections_by_document.return_value = []
        
        retriever = BM25Retriever(mock_db)
        results = retriever.retrieve("doc123", "test query", top_k=5)
        
        assert results == []

    def test_retrieve_with_sections(self):
        """Test retrieval with mock sections."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "Sustainable Investment",
                "text": "This section discusses sustainable investment and ESG criteria.",
                "page_start": 1,
            },
            {
                "section_id": "s2",
                "document_id": "doc123",
                "title": "Risk Factors",
                "text": "This section discusses various risk factors and market volatility.",
                "page_start": 5,
            },
            {
                "section_id": "s3",
                "document_id": "doc123",
                "title": "DNSH Principle",
                "text": "Do No Significant Harm principle ensures environmental protection.",
                "page_start": 10,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        results = retriever.retrieve("doc123", "sustainable investment ESG", top_k=2)
        
        assert len(results) <= 2
        # First result should be most relevant (section 1)
        if results:
            assert results[0][0]["section_id"] == "s1"

    def test_retrieve_by_keywords(self):
        """Test keyword-based retrieval."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "DNSH",
                "text": "Do No Significant Harm is important for sustainable investment.",
                "page_start": 1,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        results = retriever.retrieve_by_keywords("doc123", ["DNSH", "harm"], top_k=5)
        
        assert len(results) == 1
        assert results[0][0]["section_id"] == "s1"
