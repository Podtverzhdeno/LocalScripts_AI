"""
Strategy registry — maps strategy names to classes.

Usage:
    strategy = get_strategy("reflect", llm)
    result = strategy.run("write fibonacci in Lua")
"""

import logging
from typing import Type

from langchain_core.language_models import BaseChatModel

from strategies.base import ReasoningStrategy, PassthroughStrategy
from strategies.reflect import ReflectStrategy
from strategies.cot import ChainOfThoughtStrategy

logger = logging.getLogger("localscript.strategies")

# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, Type[ReasoningStrategy]] = {
    "none": PassthroughStrategy,
    "reflect": ReflectStrategy,
    "cot": ChainOfThoughtStrategy,
}


def register_strategy(cls: Type[ReasoningStrategy]) -> Type[ReasoningStrategy]:
    """Decorator to register a custom strategy."""
    _REGISTRY[cls.name] = cls
    logger.info("Registered strategy: %s", cls.name)
    return cls


def get_strategy(name: str, llm: BaseChatModel) -> ReasoningStrategy:
    """
    Create a strategy instance by name.

    Args:
        name: Strategy name ("none", "reflect", "cot").
        llm: LLM to use for reasoning calls.

    Returns:
        Configured ReasoningStrategy instance.

    Raises:
        ValueError: If strategy name is unknown.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown strategy: {name!r}. Available: {available}")
    return cls(llm)


def list_strategies() -> dict[str, str]:
    """Return {name: description} for all registered strategies."""
    return {name: cls.description for name, cls in sorted(_REGISTRY.items())}
