"""Unit tests for retrieval layer."""

import pytest
from unittest.mock import Mock
from src.retrieval import BM25Retriever


@pytest.mark.unit
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

    def test_index_document(self):
        """Test building BM25 index for a document."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "Test",
                "text": "This is test content",
                "page_start": 1,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        retriever.index_document("doc123")
        
        # Verify index was created
        assert "doc123" in retriever.bm25_by_doc
        assert "doc123" in retriever.sections_by_doc

    def test_retrieve_top_k(self):
        """Test limiting retrieval results to top-k."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": f"s{i}",
                "document_id": "doc123",
                "title": f"Section {i}",
                "text": f"Content about sustainable investment topic {i}",
                "page_start": i,
            }
            for i in range(10)
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        
        # Test different k values
        results_3 = retriever.retrieve("doc123", "sustainable investment", top_k=3)
        assert len(results_3) == 3
        
        results_5 = retriever.retrieve("doc123", "sustainable investment", top_k=5)
        assert len(results_5) == 5
        
        results_all = retriever.retrieve("doc123", "sustainable investment", top_k=20)
        assert len(results_all) == 10  # Only 10 sections exist

    def test_scoring_relevance(self):
        """Test BM25 scoring and relevance ranking."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "highly_relevant",
                "document_id": "doc123",
                "title": "Sustainable Investment",
                "text": "Sustainable investment sustainable investment ESG sustainable",
                "page_start": 1,
            },
            {
                "section_id": "less_relevant",
                "document_id": "doc123",
                "title": "Other Topic",
                "text": "This section discusses other topics not related to the query.",
                "page_start": 2,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        results = retriever.retrieve("doc123", "sustainable investment", top_k=2)
        
        # Most relevant should come first
        assert results[0][0]["section_id"] == "highly_relevant"
        # Score should be higher for more relevant section
        assert results[0][1] > results[1][1]

    def test_tokenization(self):
        """Test query tokenization."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "Test",
                "text": "Environmental Social Governance ESG",
                "page_start": 1,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        
        # Test with multi-word query
        results = retriever.retrieve("doc123", "Environmental Social Governance", top_k=5)
        assert len(results) == 1

    def test_multiple_documents(self):
        """Test indexing and retrieving from multiple documents."""
        mock_db = Mock()
        
        def get_sections(doc_id):
            sections = {
                "doc1": [
                    {
                        "section_id": "doc1_s1",
                        "document_id": "doc1",
                        "title": "Section 1",
                        "text": "Content about climate change",
                        "page_start": 1,
                    },
                ],
                "doc2": [
                    {
                        "section_id": "doc2_s1",
                        "document_id": "doc2",
                        "title": "Section 1",
                        "text": "Content about sustainable investment",
                        "page_start": 1,
                    },
                ],
            }
            return sections.get(doc_id, [])
        
        mock_db.get_sections_by_document.side_effect = get_sections
        
        retriever = BM25Retriever(mock_db)
        
        # Index both documents
        retriever.index_document("doc1")
        retriever.index_document("doc2")
        
        # Verify both are indexed
        assert "doc1" in retriever.bm25_by_doc
        assert "doc2" in retriever.bm25_by_doc
        
        # Retrieve from each
        results1 = retriever.retrieve("doc1", "climate change", top_k=5)
        assert len(results1) == 1
        assert results1[0][0]["document_id"] == "doc1"
        
        results2 = retriever.retrieve("doc2", "sustainable investment", top_k=5)
        assert len(results2) == 1
        assert results2[0][0]["document_id"] == "doc2"

    def test_case_insensitive_search(self):
        """Test that search is case-insensitive."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "DNSH",
                "text": "Do No Significant HARM principle",
                "page_start": 1,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        
        # Search with different cases
        results_lower = retriever.retrieve("doc123", "harm principle", top_k=5)
        results_upper = retriever.retrieve("doc123", "HARM PRINCIPLE", top_k=5)
        results_mixed = retriever.retrieve("doc123", "Harm Principle", top_k=5)
        
        # All should return the same section
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    def test_auto_indexing_on_first_retrieve(self):
        """Test that documents are auto-indexed on first retrieval."""
        mock_db = Mock()
        mock_sections = [
            {
                "section_id": "s1",
                "document_id": "doc123",
                "title": "Test",
                "text": "Test content",
                "page_start": 1,
            },
        ]
        mock_db.get_sections_by_document.return_value = mock_sections
        
        retriever = BM25Retriever(mock_db)
        
        # Document not indexed yet
        assert "doc123" not in retriever.bm25_by_doc
        
        # First retrieve should trigger indexing
        results = retriever.retrieve("doc123", "test", top_k=5)
        
        # Now it should be indexed
        assert "doc123" in retriever.bm25_by_doc
        assert len(results) == 1
