"""Factory for creating LLM workers."""

from .base import LLMWorker
from .nemotron import NemotronWorker
from .ollama import OllamaWorker
from ..config import get_settings


def get_worker(use_ollama: bool = None) -> LLMWorker:
    """
    Get appropriate LLM worker based on configuration.
    
    Args:
        use_ollama: Override to force Ollama. If None, uses settings.
        
    Returns:
        LLM worker instance
    """
    settings = get_settings()
    
    if use_ollama is None:
        use_ollama = settings.use_ollama
    
    if use_ollama:
        return OllamaWorker()
    else:
        return NemotronWorker()
