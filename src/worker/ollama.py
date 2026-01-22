"""Ollama worker client for local testing."""

import json
import httpx
from typing import Dict, Any, Optional

from .base import LLMWorker
from ..config import get_settings


class OllamaWorker(LLMWorker):
    """Ollama worker for local testing (Qwen3:8b)."""

    def __init__(self):
        """Initialize Ollama worker."""
        self.settings = get_settings()
        self.api_url = self.settings.ollama_api_url.rstrip("/")
        self.model = self.settings.ollama_model
        self.timeout = self.settings.ollama_timeout

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """Generate text using Ollama."""
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if json_mode:
            payload["format"] = "json"

        # Make request
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.api_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        result = response.json()
        return result["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """Generate structured JSON using Ollama."""
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        return json.loads(response)
