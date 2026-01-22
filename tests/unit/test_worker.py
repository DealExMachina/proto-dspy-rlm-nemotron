"""Unit tests for LLM workers."""

import pytest
import json
import httpx
from unittest.mock import Mock, patch, MagicMock
from src.worker.ollama import OllamaWorker
from src.worker.nemotron import NemotronWorker
from src.worker.factory import get_worker


class TestOllamaWorker:
    """Test Ollama worker (used for local testing)."""

    @patch("src.worker.ollama.httpx.Client")
    def test_generate(self, mock_client):
        """Test basic text generation."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "This is a test response"}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Test
        worker = OllamaWorker()
        result = worker.generate("Test prompt")
        
        assert result == "This is a test response"
        mock_client_instance.post.assert_called_once()

    @patch("src.worker.ollama.httpx.Client")
    def test_generate_json(self, mock_client):
        """Test JSON generation."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": '{"key": "value", "number": 42}'}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Test
        worker = OllamaWorker()
        result = worker.generate_json("Test prompt")
        
        assert result == {"key": "value", "number": 42}
        mock_client_instance.post.assert_called_once()

    @patch("src.worker.ollama.httpx.Client")
    def test_generate_with_system_prompt(self, mock_client):
        """Test generation with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Response with system prompt"}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OllamaWorker()
        result = worker.generate(
            "User prompt",
            system_prompt="You are a helpful assistant"
        )
        
        assert result == "Response with system prompt"
        
        # Verify system prompt was included in messages
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    @patch("src.worker.ollama.httpx.Client")
    def test_generate_error_handling(self, mock_client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock()
        )
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OllamaWorker()
        
        with pytest.raises(httpx.HTTPStatusError):
            worker.generate("Test prompt")

    @patch("src.worker.ollama.httpx.Client")
    def test_json_mode_flag(self, mock_client):
        """Test JSON mode parameter is passed correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": '{"result": "json mode"}'}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OllamaWorker()
        result = worker.generate("Test prompt", json_mode=True)
        
        # Verify format=json was set
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["format"] == "json"

    @patch("src.worker.ollama.httpx.Client")
    def test_temperature_control(self, mock_client):
        """Test temperature parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = OllamaWorker()
        worker.generate("Test prompt", temperature=0.7)
        
        # Verify temperature was set
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.7


class TestNemotronWorker:
    """Test Nemotron worker on Koyeb H100."""

    @patch("src.worker.nemotron.httpx.Client")
    def test_nemotron_generate(self, mock_client):
        """Test basic Nemotron generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Nemotron response"}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = NemotronWorker()
        result = worker.generate("Test prompt")
        
        assert result == "Nemotron response"
        mock_client_instance.post.assert_called_once()

    @patch("src.worker.nemotron.httpx.Client")
    def test_nemotron_json_output(self, mock_client):
        """Test Nemotron JSON generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": '{"article": "8", "confidence": "0.9"}'}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = NemotronWorker()
        result = worker.generate_json("Extract article")
        
        assert result == {"article": "8", "confidence": "0.9"}

    @patch("src.worker.nemotron.httpx.Client")
    def test_nemotron_api_format(self, mock_client):
        """Test Nemotron uses OpenAI-compatible format."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test"}}]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = NemotronWorker()
        worker.generate("Test", json_mode=True)
        
        # Verify OpenAI-compatible format
        call_args = mock_client_instance.post.call_args
        assert "/v1/chat/completions" in call_args[0][0]
        
        payload = call_args[1]["json"]
        assert "model" in payload
        assert "messages" in payload
        assert "response_format" in payload
        assert payload["response_format"]["type"] == "json_object"

    @patch("src.worker.nemotron.httpx.Client")
    def test_nemotron_timeout(self, mock_client):
        """Test Nemotron timeout configuration."""
        mock_client_instance = Mock()
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = NemotronWorker()
        
        # Check timeout is configured
        assert worker.timeout == worker.settings.nemotron_timeout

    @patch("src.worker.nemotron.httpx.Client")
    def test_nemotron_error_response(self, mock_client):
        """Test Nemotron error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "API Error", request=Mock(), response=Mock()
        )
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        worker = NemotronWorker()
        
        with pytest.raises(httpx.HTTPStatusError):
            worker.generate("Test prompt")


class TestWorkerFactory:
    """Test worker factory."""

    @patch.dict("os.environ", {"USE_OLLAMA": "true"})
    def test_get_worker_ollama(self):
        """Test getting Ollama worker with OpenAI API."""
        from src.worker.openai_compatible import OpenAICompatibleWorker
        
        # Default uses OpenAI-compatible API
        worker = get_worker(use_ollama=True)
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "localhost" in worker.api_url
        
        # Legacy API still available
        worker_legacy = get_worker(use_ollama=True, use_openai_api=False)
        assert isinstance(worker_legacy, OllamaWorker)

    @patch.dict("os.environ", {"USE_OLLAMA": "false"})
    def test_get_worker_nemotron(self):
        """Test getting Nemotron worker with OpenAI API."""
        from src.worker.openai_compatible import OpenAICompatibleWorker
        
        # Default uses OpenAI-compatible API
        worker = get_worker(use_ollama=False)
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "koyeb" in worker.api_url
        
        # Legacy API still available
        worker_legacy = get_worker(use_ollama=False, use_openai_api=False)
        assert isinstance(worker_legacy, NemotronWorker)

    @patch.dict("os.environ", {"USE_OLLAMA": "true"})
    def test_get_worker_override(self):
        """Test overriding default worker selection."""
        from src.worker.openai_compatible import OpenAICompatibleWorker
        
        # Settings say use Ollama, but we override to Nemotron
        worker = get_worker(use_ollama=False)
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "koyeb" in worker.api_url
        
        # Override to Ollama
        worker = get_worker(use_ollama=True)
        assert isinstance(worker, OpenAICompatibleWorker)
        assert "localhost" in worker.api_url
