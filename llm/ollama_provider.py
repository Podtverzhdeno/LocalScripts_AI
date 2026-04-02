"""Ollama provider — local LLM backend, no API key needed."""
import os
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel


def make_ollama_llm(model: str, temperature: float = 0.2) -> BaseChatModel:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(model=model, base_url=base_url, temperature=temperature)
