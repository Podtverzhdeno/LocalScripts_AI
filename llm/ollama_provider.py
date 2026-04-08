"""Ollama provider — local LLM backend, no API key needed."""
import os
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel


def make_ollama_llm(model: str, temperature: float = 0.2, streaming: bool = False, callbacks=None) -> BaseChatModel:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # Add timeout to prevent hanging on slow responses (especially for approver)
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))  # 60s default
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
        timeout=timeout,
        streaming=streaming,
        callbacks=callbacks or []
    )
