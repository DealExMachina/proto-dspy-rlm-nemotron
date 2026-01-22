"""OpenAI-compatible LLM worker for Ollama and Nemotron."""

import json
import httpx
from typing import Dict, Any, Optional

from .base import LLMWorker
from ..config import get_settings


class OpenAICompatibleWorker(LLMWorker):
    """
    Unified worker for OpenAI-compatible APIs.
    
    Works with:
    - Ollama (localhost via /v1/chat/completions)
    - Nemotron on Koyeb (vLLM via /v1/chat/completions)
    - Any OpenAI-compatible endpoint
    """

    def __init__(self, api_url: str, model_name: str, timeout: int = 60):
        """
        Initialize OpenAI-compatible worker.
        
        Args:
            api_url: Base URL for the API (e.g., "http://localhost:11434")
            model_name: Model identifier (e.g., "qwen2.5:3b", "nvidia/nemotron-3-8b-instruct")
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """Generate text using OpenAI-compatible API."""
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add JSON mode if requested
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        # Make request to OpenAI-compatible endpoint
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        # Parse OpenAI-compatible response
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """Generate structured JSON using OpenAI-compatible API."""
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        return json.loads(response)


def create_ollama_worker() -> OpenAICompatibleWorker:
    """Create worker for local Ollama."""
    settings = get_settings()
    return OpenAICompatibleWorker(
        api_url=settings.ollama_api_url,
        model_name=settings.ollama_model,
        timeout=settings.ollama_timeout,
    )


def create_nemotron_worker() -> OpenAICompatibleWorker:
    """Create worker for Nemotron on Koyeb."""
    settings = get_settings()
    return OpenAICompatibleWorker(
        api_url=settings.nemotron_api_url,
        model_name="nvidia/nemotron-3-8b-instruct",  # Koyeb model name
        timeout=settings.nemotron_timeout,
    )
