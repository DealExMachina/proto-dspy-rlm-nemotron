"""Factory for creating LLM workers."""

from .base import LLMWorker
from .nemotron import NemotronWorker
from .ollama import OllamaWorker
from .openai_compatible import OpenAICompatibleWorker, create_ollama_worker, create_nemotron_worker
from ..config import get_settings


def get_worker(use_ollama: bool = None, use_openai_api: bool = True) -> LLMWorker:
    """
    Get appropriate LLM worker based on configuration.
    
    Args:
        use_ollama: Override to force Ollama. If None, uses settings.
        use_openai_api: Use OpenAI-compatible API (recommended). If False, uses legacy API.
        
    Returns:
        LLM worker instance
        
    Note:
        The OpenAI-compatible API (/v1/chat/completions) is now the default and 
        recommended approach as it works consistently with both Ollama and Nemotron/Koyeb.
    """
    settings = get_settings()
    
    if use_ollama is None:
        use_ollama = settings.use_ollama
    
    # Use OpenAI-compatible API by default (works for both Ollama and Nemotron)
    if use_openai_api:
        if use_ollama:
            return create_ollama_worker()
        else:
            return create_nemotron_worker()
    else:
        # Legacy API support (deprecated)
        if use_ollama:
            return OllamaWorker()
        else:
            return NemotronWorker()
