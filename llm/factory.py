"""
LLMFactory — single entry point for LLM backend selection.
Switch backends by setting LLM_BACKEND env var or editing config/settings.yaml.
"""

import os
from langchain_core.language_models import BaseChatModel
from config.loader import load_settings


def get_llm() -> BaseChatModel:
    """
    Returns the configured LLM backend.
    Priority: LLM_BACKEND env var > settings.yaml
    """
    settings = load_settings()
    backend = os.getenv("LLM_BACKEND", settings["llm"]["backend"]).lower()
    model = os.getenv("LLM_MODEL", settings["llm"]["model"])
    temperature = settings["llm"].get("temperature", 0.2)

    if backend == "openai":
        from llm.openai_provider import make_openai_llm
        return make_openai_llm(model, temperature)
    elif backend == "openrouter":
        from llm.openrouter_provider import make_openrouter_llm
        return make_openrouter_llm(model, temperature)
    elif backend == "anthropic":
        from llm.anthropic_provider import make_anthropic_llm
        return make_anthropic_llm(model, temperature)
    elif backend == "ollama":
        from llm.ollama_provider import make_ollama_llm
        return make_ollama_llm(model, temperature)
    else:
        raise ValueError(f"Unknown LLM backend: {backend!r}. Use 'openai', 'openrouter', 'anthropic' or 'ollama'.")
