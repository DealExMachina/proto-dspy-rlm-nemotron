"""Unit tests for OpenAI-compatible worker."""

import pytest
import json
import httpx
from unittest.mock import Mock, patch
from src.worker.openai_compatible import (
    OpenAICompatibleWorker,
    create_ollama_worker,
    create_nemotron_worker,
)


@pytest.mark.unit
class TestOpenAICompatibleWorker:
    """Test unified OpenAI-compatible worker."""

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_generate_basic(self, mock_client):
        """Test basic text generation with OpenAI API format."""
        # Mock OpenAI-compatible response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a response"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Test
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="qwen2.5:3b-instruct",
            timeout=60
        )
        result = worker.generate("Test prompt")
        
        assert result == "This is a response"
        mock_client_instance.post.assert_called_once()
        
        # Verify OpenAI-compatible endpoint
        call_args = mock_client_instance.post.call_args
        assert "/v1/chat/completions" in call_args[0][0]

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_generate_with_system_prompt(self, mock_client):
        """Test generation with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="qwen2.5:3b-instruct",
            timeout=60
        )
        result = worker.generate(
            "User prompt",
            system_prompt="You are a helpful assistant"
        )
        
        # Verify messages format
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_generate_json(self, mock_client):
        """Test JSON generation with response_format."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"article": "8", "confidence": 0.9}'
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="qwen2.5:3b-instruct",
            timeout=60
        )
        result = worker.generate_json("Extract data")
        
        assert result == {"article": "8", "confidence": 0.9}
        
        # Verify response_format was set
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["response_format"]["type"] == "json_object"

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_temperature_parameter(self, mock_client):
        """Test temperature parameter is passed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test"}}]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="test-model",
            timeout=60
        )
        worker.generate("Test", temperature=0.8)
        
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.8

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_max_tokens_parameter(self, mock_client):
        """Test max_tokens parameter is passed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test"}}]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="test-model",
            timeout=60
        )
        worker.generate("Test", max_tokens=500)
        
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["max_tokens"] == 500

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_error_handling(self, mock_client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock()
        )
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="test-model",
            timeout=60
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            worker.generate("Test")

    def test_create_ollama_worker(self):
        """Test Ollama worker factory."""
        worker = create_ollama_worker()
        
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "localhost" in worker.api_url
        assert "qwen" in worker.model_name.lower()

    def test_create_nemotron_worker(self):
        """Test Nemotron worker factory."""
        worker = create_nemotron_worker()
        
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "koyeb.app" in worker.api_url
        assert "nemotron" in worker.model_name.lower()

    def test_api_url_normalization(self):
        """Test that API URL is normalized (trailing slash removed)."""
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434/",
            model_name="test-model",
            timeout=60
        )
        
        # Trailing slash should be removed
        assert not worker.api_url.endswith("/")
        assert worker.api_url == "http://localhost:11434"

    @patch("src.worker.openai_compatible.httpx.Client")
    def test_model_name_in_payload(self, mock_client):
        """Test that model name is included in request."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test"}}]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OpenAICompatibleWorker(
            api_url="http://localhost:11434",
            model_name="custom-model-name",
            timeout=60
        )
        worker.generate("Test")
        
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "custom-model-name"


@pytest.mark.unit
class TestDSPyIntegration:
    """Test DSPy integration helpers."""

    @patch("src.worker.dspy_integration.dspy.OllamaLocal")
    def test_configure_dspy_for_ollama(self, mock_ollama):
        """Test DSPy Ollama configuration."""
        from src.worker.dspy_integration import configure_dspy_for_ollama
        
        mock_lm = Mock()
        mock_ollama.return_value = mock_lm
        
        configure_dspy_for_ollama()
        
        # Should create OllamaLocal instance
        mock_ollama.assert_called_once()
        call_kwargs = mock_ollama.call_args[1]
        assert "model" in call_kwargs
        assert "base_url" in call_kwargs

    @patch("src.worker.dspy_integration.dspy.OpenAI")
    def test_configure_dspy_for_nemotron(self, mock_openai):
        """Test DSPy Nemotron configuration."""
        from src.worker.dspy_integration import configure_dspy_for_nemotron
        
        mock_lm = Mock()
        mock_openai.return_value = mock_lm
        
        configure_dspy_for_nemotron()
        
        # Should create OpenAI instance with custom api_base
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert "model" in call_kwargs
        assert "api_base" in call_kwargs
        assert "nemotron" in call_kwargs["model"].lower()

    @patch("src.worker.dspy_integration.configure_dspy_for_ollama")
    @patch.dict("os.environ", {"USE_OLLAMA": "true"})
    def test_configure_dspy_auto_ollama(self, mock_configure):
        """Test auto-configuration chooses Ollama."""
        from src.worker.dspy_integration import configure_dspy_auto
        
        configure_dspy_auto(use_ollama=True)
        
        mock_configure.assert_called_once()

    @patch("src.worker.dspy_integration.configure_dspy_for_nemotron")
    @patch.dict("os.environ", {"USE_OLLAMA": "false"})
    def test_configure_dspy_auto_nemotron(self, mock_configure):
        """Test auto-configuration chooses Nemotron."""
        from src.worker.dspy_integration import configure_dspy_auto
        
        configure_dspy_auto(use_ollama=False)
        
        mock_configure.assert_called_once()
