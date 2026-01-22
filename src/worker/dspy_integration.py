"""DSPy integration helpers for configuring LM backends."""

import dspy
from typing import Optional
from .base import LLMWorker
from ..config import get_settings


def configure_dspy_for_ollama() -> None:
    """
    Configure DSPy to use local Ollama.
    
    Uses DSPy 2.4.9's OllamaLocal class which works with Ollama's native API.
    """
    settings = get_settings()
    
    lm = dspy.OllamaLocal(
        model=settings.ollama_model,
        base_url=settings.ollama_api_url,
        timeout_s=settings.ollama_timeout,
    )
    
    dspy.configure(lm=lm)


def configure_dspy_for_nemotron() -> None:
    """
    Configure DSPy to use Nemotron on Koyeb (vLLM).
    
    Uses OpenAI-compatible endpoint since vLLM implements OpenAI API.
    """
    settings = get_settings()
    
    # For DSPy 2.4.9: Use OpenAI class with custom api_base
    # The vLLM server on Koyeb implements OpenAI-compatible API
    lm = dspy.OpenAI(
        model="nvidia/nemotron-3-8b-instruct",
        api_base=f"{settings.nemotron_api_url}/v1",
        api_key="dummy",  # vLLM doesn't require real key
        model_type="chat",
        timeout=settings.nemotron_timeout,
    )
    
    dspy.configure(lm=lm)


def configure_dspy_auto(use_ollama: Optional[bool] = None) -> None:
    """
    Auto-configure DSPy based on settings.
    
    Args:
        use_ollama: Override to force Ollama. If None, uses settings.
    """
    settings = get_settings()
    
    if use_ollama is None:
        use_ollama = settings.use_ollama
    
    if use_ollama:
        configure_dspy_for_ollama()
    else:
        configure_dspy_for_nemotron()


# DSPy 3.x Migration Notes:
# When upgrading to DSPy 3.x, replace above with:
#
# def configure_dspy_for_ollama_v3():
#     """DSPy 3.x version"""
#     settings = get_settings()
#     lm = dspy.LM(
#         model=f'ollama_chat/{settings.ollama_model}',
#         api_base=settings.ollama_api_url
#     )
#     dspy.configure(lm=lm)
#
# def configure_dspy_for_nemotron_v3():
#     """DSPy 3.x version"""
#     settings = get_settings()
#     lm = dspy.LM(
#         model='openai/nvidia/nemotron-3-8b-instruct',
#         api_base=f"{settings.nemotron_api_url}/v1",
#         api_key=''
#     )
#     dspy.configure(lm=lm)
