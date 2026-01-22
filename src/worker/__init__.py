"""LLM worker clients for Nemotron and Ollama."""

from .base import LLMWorker
from .nemotron import NemotronWorker
from .ollama import OllamaWorker
from .openai_compatible import OpenAICompatibleWorker, create_ollama_worker, create_nemotron_worker
from .factory import get_worker
from .dspy_integration import configure_dspy_auto, configure_dspy_for_ollama, configure_dspy_for_nemotron

__all__ = [
    "LLMWorker",
    "NemotronWorker",
    "OllamaWorker",
    "OpenAICompatibleWorker",
    "create_ollama_worker",
    "create_nemotron_worker",
    "get_worker",
    "configure_dspy_auto",
    "configure_dspy_for_ollama",
    "configure_dspy_for_nemotron",
]
