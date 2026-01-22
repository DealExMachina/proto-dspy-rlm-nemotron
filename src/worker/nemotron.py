"""Nemotron worker client for Koyeb."""

import json
import httpx
from typing import Dict, Any, Optional

from .base import LLMWorker
from ..config import get_settings


class NemotronWorker(LLMWorker):
    """Nemotron worker on Koyeb H100."""

    def __init__(self):
        """Initialize Nemotron worker."""
        self.settings = get_settings()
        self.api_url = self.settings.nemotron_api_url.rstrip("/")
        self.timeout = self.settings.nemotron_timeout

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """Generate text using Nemotron."""
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Prepare request payload
        payload = {
            "model": "nvidia/nemotron-3-8b-instruct",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        # Make request
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """Generate structured JSON using Nemotron."""
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        return json.loads(response)
