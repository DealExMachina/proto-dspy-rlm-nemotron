"""Unit tests for RLM controller."""

import pytest
from unittest.mock import Mock, patch
from src.controller import RLMController
from src.models import (
    SFDRState,
    SustainableInvestmentDefinition,
    DNSHField,
    DNSHCoverage,
    PAIField,
)


@pytest.mark.unit
class TestRLMController:
    """Test RLM controller extraction methods."""

    def test_extract_article_classification(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test SFDR article classification extraction."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        article, confidence = controller.extract_article_classification("test_doc_123")
        
        # Should extract article
        assert article in ["6", "8", "9"]
        assert 0.0 <= confidence <= 1.0
        
        # Should have called retriever
        mock_retriever.retrieve.assert_called_once()

    def test_extract_definition(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test sustainable investment definition extraction."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        definition = controller.extract_sustainable_investment_definition("test_doc_123")
        
        # Should return definition object
        assert definition is not None
        assert isinstance(definition, SustainableInvestmentDefinition)
        assert definition.present is True
        assert definition.confidence > 0

    def test_extract_dnsh(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test DNSH information extraction."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        dnsh = controller.extract_dnsh("test_doc_123")
        
        # Should return DNSH field
        assert dnsh is not None
        assert isinstance(dnsh, DNSHField)
        assert dnsh.coverage in [DNSHCoverage.NONE, DNSHCoverage.PARTIAL, DNSHCoverage.FULL]
        assert 0.0 <= dnsh.confidence <= 1.0

    def test_extract_pai(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test PAI coverage extraction."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        pai = controller.extract_pai("test_doc_123")
        
        # Should return PAI field
        assert pai is not None
        assert isinstance(pai, PAIField)
        if pai.mandatory_coverage_ratio is not None:
            assert 0.0 <= pai.mandatory_coverage_ratio <= 1.0

    def test_missing_fields_tracking(self, temp_db_memory, mock_ollama_worker):
        """Test tracking of missing fields."""
        # Mock retriever that returns empty results
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        state = controller.build_sfdr_state(
            document_id="test_doc_123",
            isin="LU1234567890",
            doc_version="1"
        )
        
        # Should track missing fields
        assert isinstance(state.missing_fields, list)
        # With empty retrieval, most fields should be missing
        assert len(state.missing_fields) > 0

    def test_confidence_calculation(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test overall confidence calculation."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        state = controller.build_sfdr_state(
            document_id="test_doc_123",
            isin="LU1234567890",
            doc_version="1"
        )
        
        # Overall confidence should be within bounds
        assert 0.0 <= state.confidence <= 1.0
        
        # Should be average of field confidences
        confidences = []
        if state.sustainable_investment_definition:
            confidences.append(state.sustainable_investment_definition.confidence)
        if state.dnsh:
            confidences.append(state.dnsh.confidence)
        if state.pai:
            confidences.append(state.pai.confidence)
        
        if confidences:
            expected_confidence = sum(confidences) / (len(confidences) + 1)  # +1 for article
            # Allow some tolerance for floating point arithmetic
            assert abs(state.confidence - expected_confidence) < 0.1

    def test_citation_creation(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test that citations are created with results."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        definition = controller.extract_sustainable_investment_definition("test_doc_123")
        
        # Should have citations
        assert definition is not None
        assert len(definition.citations) > 0
        
        # Citations should have required fields
        citation = definition.citations[0]
        assert citation.document_id == "test_doc_123"
        assert citation.page_number > 0
        assert len(citation.text_snippet) > 0

    def test_no_results_from_retrieval(self, temp_db_memory, mock_ollama_worker):
        """Test handling when retrieval returns no results."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        # Article classification
        article, conf = controller.extract_article_classification("test_doc_123")
        assert article is None
        assert conf == 0.0
        
        # Definition
        definition = controller.extract_sustainable_investment_definition("test_doc_123")
        assert definition is None
        
        # DNSH
        dnsh = controller.extract_dnsh("test_doc_123")
        assert dnsh is not None  # Returns default DNSH object
        assert dnsh.present is False

    def test_build_sfdr_state_complete(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test building complete SFDR state."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        state = controller.build_sfdr_state(
            document_id="test_doc_123",
            isin="LU1234567890",
            doc_version="1"
        )
        
        # Should create state
        assert isinstance(state, SFDRState)
        assert state.fund_isin == "LU1234567890"
        assert state.doc_version == "1"
        assert state.state_id is not None
        
        # Should have extracted fields
        assert state.claimed_article in ["6", "8", "9", None]
        
        # Should track documents
        assert "test_doc_123" in state.documents

    def test_extraction_with_multiple_retrieval_calls(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test that each extraction makes appropriate retrieval calls."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        # Build full state
        state = controller.build_sfdr_state(
            document_id="test_doc_123",
            isin="LU1234567890",
            doc_version="1"
        )
        
        # Should have made multiple retrieval calls for different fields
        assert mock_retriever.retrieve.call_count >= 4  # article, definition, dnsh, pai

    def test_worker_error_handling(self, temp_db_memory, mock_retrieval_results):
        """Test handling when worker raises errors."""
        mock_worker = Mock()
        mock_worker.generate.side_effect = Exception("Worker error")
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_worker)
        
        # Should handle errors gracefully
        article, conf = controller.extract_article_classification("test_doc_123")
        assert article is None
        assert conf == 0.0

    def test_dnsh_coverage_mapping(self, temp_db_memory, mock_retrieval_results):
        """Test DNSH coverage string to enum mapping."""
        # Create worker that returns different coverage levels
        mock_worker = Mock()
        
        def mock_generate_json(prompt, **kwargs):
            if "dnsh" in prompt.lower():
                return {
                    "dnsh_present": "true",
                    "coverage": "partial",
                    "confidence": "0.8",
                }
            return {}
        
        mock_worker.generate_json.side_effect = mock_generate_json
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_worker)
        
        dnsh = controller.extract_dnsh("test_doc_123")
        
        # Should map "partial" to PARTIAL enum
        assert dnsh.coverage == DNSHCoverage.PARTIAL

    def test_pai_ratio_parsing(self, temp_db_memory, mock_retrieval_results):
        """Test PAI ratio parsing from string."""
        mock_worker = Mock()
        
        def mock_generate_json(prompt, **kwargs):
            if "pai" in prompt.lower():
                return {
                    "mandatory_coverage_ratio": "0.85",
                    "confidence": "0.9",
                }
            return {}
        
        mock_worker.generate_json.side_effect = mock_generate_json
        
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_worker)
        
        pai = controller.extract_pai("test_doc_123")
        
        # Should parse string to float
        assert pai is not None
        assert pai.mandatory_coverage_ratio == 0.85

    def test_state_id_generation(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test that each state gets unique ID."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        state1 = controller.build_sfdr_state("doc1", "LU1", "1")
        state2 = controller.build_sfdr_state("doc2", "LU2", "1")
        
        # Each state should have unique ID
        assert state1.state_id != state2.state_id

    def test_dspy_integration(self, temp_db_memory, mock_ollama_worker, mock_retrieval_results):
        """Test DSPy signatures are used correctly."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = mock_retrieval_results[:3]
        
        controller = RLMController(temp_db_memory, mock_retriever, mock_ollama_worker)
        
        # Extraction should work with DSPy signatures
        with patch('dspy.Predict') as mock_predict:
            mock_result = Mock()
            mock_result.article = "8"
            mock_result.confidence = "0.9"
            
            mock_predict_instance = Mock()
            mock_predict_instance.return_value = mock_result
            mock_predict.return_value = mock_predict_instance
            
            article, conf = controller.extract_article_classification("test_doc_123")
            
            # DSPy Predict should have been called
            mock_predict.assert_called()
