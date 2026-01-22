"""Unit tests for DSPy signatures."""

import pytest
import dspy
from src.controller.dspy_signatures import (
    ClassifyArticle,
    ExtractDefinition,
    ExtractDNSH,
    ExtractPAI,
)


@pytest.mark.unit
class TestDSPySignatures:
    """Test DSPy signature definitions."""

    def test_classify_article_signature(self):
        """Test ClassifyArticle signature has correct fields."""
        # Check input fields
        assert "context" in ClassifyArticle.input_fields
        
        # Check output fields
        assert "article" in ClassifyArticle.output_fields
        assert "confidence" in ClassifyArticle.output_fields
        assert "reasoning" in ClassifyArticle.output_fields

    def test_extract_definition_signature(self):
        """Test ExtractDefinition signature has correct fields."""
        # Check input fields
        assert "context" in ExtractDefinition.input_fields
        
        # Check output fields
        assert "definition_present" in ExtractDefinition.output_fields
        assert "definition_text" in ExtractDefinition.output_fields
        assert "page_number" in ExtractDefinition.output_fields
        assert "confidence" in ExtractDefinition.output_fields

    def test_extract_dnsh_signature(self):
        """Test ExtractDNSH signature has correct fields."""
        # Check input fields
        assert "context" in ExtractDNSH.input_fields
        
        # Check output fields
        assert "dnsh_present" in ExtractDNSH.output_fields
        assert "coverage" in ExtractDNSH.output_fields
        assert "page_number" in ExtractDNSH.output_fields
        assert "confidence" in ExtractDNSH.output_fields

    def test_extract_pai_signature(self):
        """Test ExtractPAI signature has correct fields."""
        # Check input fields
        assert "context" in ExtractPAI.input_fields
        
        # Check output fields
        assert "mandatory_coverage_ratio" in ExtractPAI.output_fields
        assert "page_number" in ExtractPAI.output_fields
        assert "confidence" in ExtractPAI.output_fields

    def test_signature_input_fields_have_descriptions(self):
        """Test that input fields have descriptions."""
        # All signatures should have context with description
        for signature_class in [ClassifyArticle, ExtractDefinition, ExtractDNSH, ExtractPAI]:
            context_field = signature_class.input_fields["context"]
            assert hasattr(context_field, "json_schema_extra")
            assert "desc" in context_field.json_schema_extra

    def test_signature_output_fields_have_descriptions(self):
        """Test that output fields have descriptions."""
        # Check ClassifyArticle outputs
        article_field = ClassifyArticle.output_fields["article"]
        assert hasattr(article_field, "json_schema_extra")
        assert "desc" in article_field.json_schema_extra
        
        # Check ExtractDefinition outputs
        definition_field = ExtractDefinition.output_fields["definition_present"]
        assert hasattr(definition_field, "json_schema_extra")
        assert "desc" in definition_field.json_schema_extra

    def test_classify_article_is_signature(self):
        """Test ClassifyArticle is a valid DSPy signature."""
        assert issubclass(ClassifyArticle, dspy.Signature)

    def test_extract_definition_is_signature(self):
        """Test ExtractDefinition is a valid DSPy signature."""
        assert issubclass(ExtractDefinition, dspy.Signature)

    def test_extract_dnsh_is_signature(self):
        """Test ExtractDNSH is a valid DSPy signature."""
        assert issubclass(ExtractDNSH, dspy.Signature)

    def test_extract_pai_is_signature(self):
        """Test ExtractPAI is a valid DSPy signature."""
        assert issubclass(ExtractPAI, dspy.Signature)
