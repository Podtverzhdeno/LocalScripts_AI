"""
LLMFactory — single entry point for LLM backend selection.

Supports per-agent model overrides via config/settings.yaml `agents:` section.
If no override is set for a role, the default `llm:` config is used.

Examples:
    get_llm()              → default model
    get_llm("generator")   → generator-specific model (or default if not configured)
"""

import logging
import os
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from config.loader import load_settings

logger = logging.getLogger("localscript.llm")

# ── Supported backends ────────────────────────────────────────────────────────

_BACKEND_FACTORIES = {
    "openai": lambda m, t: _make_openai(m, t),
    "openrouter": lambda m, t: _make_openrouter(m, t),
    "anthropic": lambda m, t: _make_anthropic(m, t),
    "ollama": lambda m, t: _make_ollama(m, t),
}


def _make_openai(model: str, temperature: float) -> BaseChatModel:
    from llm.openai_provider import make_openai_llm
    return make_openai_llm(model, temperature)


def _make_openrouter(model: str, temperature: float) -> BaseChatModel:
    from llm.openrouter_provider import make_openrouter_llm
    return make_openrouter_llm(model, temperature)


def _make_anthropic(model: str, temperature: float) -> BaseChatModel:
    from llm.anthropic_provider import make_anthropic_llm
    return make_anthropic_llm(model, temperature)


def _make_ollama(model: str, temperature: float) -> BaseChatModel:
    from llm.ollama_provider import make_ollama_llm
    return make_ollama_llm(model, temperature)


# ── Resolve config for a role ─────────────────────────────────────────────────

def _resolve_config(role: str | None = None) -> tuple[str, str, float]:
    """
    Resolve (backend, model, temperature) for a given agent role.

    Priority chain:
        1. Environment variables (LLM_BACKEND, LLM_MODEL) — always win
        2. Per-agent override in settings.yaml → agents.<role>.backend/model
        3. Default settings.yaml → llm.backend/model
    """
    settings = load_settings()
    default_cfg = settings["llm"]

    # Start with defaults
    backend = default_cfg["backend"]
    model = default_cfg["model"]
    temperature = default_cfg.get("temperature", 0.2)

    # Layer 2: per-agent override from settings.yaml
    if role:
        agent_overrides = settings.get("agents", {}).get(role, {}) or {}
        if agent_overrides.get("backend"):
            backend = agent_overrides["backend"]
        if agent_overrides.get("model"):
            model = agent_overrides["model"]
        if agent_overrides.get("temperature") is not None:
            temperature = agent_overrides["temperature"]

    # Layer 1: env vars always win (for CLI --backend flag compatibility)
    backend = os.getenv("LLM_BACKEND", backend).lower()
    model = os.getenv("LLM_MODEL", model)

    return backend, model, temperature


# ── Public API ────────────────────────────────────────────────────────────────

def get_llm(role: str | None = None) -> BaseChatModel:
    """
    Returns the configured LLM for a given agent role.

    Args:
        role: Agent role name ("generator", "validator", "reviewer").
              If None, returns the default LLM.

    Returns:
        Configured BaseChatModel instance.
    """
    backend, model, temperature = _resolve_config(role)

    factory = _BACKEND_FACTORIES.get(backend)
    if factory is None:
        supported = ", ".join(sorted(_BACKEND_FACTORIES))
        raise ValueError(f"Unknown LLM backend: {backend!r}. Supported: {supported}")

    logger.info("LLM [%s]: backend=%s, model=%s", role or "default", backend, model)
    return factory(model, temperature)
