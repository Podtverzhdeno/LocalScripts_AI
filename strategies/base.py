"""
Base class for reasoning strategies.

A strategy wraps one or more LLM calls to improve output quality
before the agent produces its final answer. Strategies are optional —
when disabled, the agent calls the LLM directly (zero overhead).
"""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage


class ReasoningStrategy(ABC):
    """
    Abstract reasoning strategy.

    Subclasses implement `run()` which takes a prompt and returns
    an improved response using multi-step LLM reasoning.
    """

    name: str = "base"
    description: str = "Abstract base strategy"

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def _call_llm(self, prompt: str, system: str | None = None) -> str:
        """Helper: single LLM call with optional system message."""
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = self.llm.invoke(messages)
        return response.content.strip()

    @abstractmethod
    def run(self, prompt: str, context: dict | None = None) -> str:
        """
        Execute the reasoning strategy.

        Args:
            prompt: The original prompt to enhance.
            context: Optional dict with extra info (task, errors, etc.)

        Returns:
            Improved LLM response after multi-step reasoning.
        """
        ...


class PassthroughStrategy(ReasoningStrategy):
    """No-op strategy — calls LLM once, returns as-is. Zero overhead."""

    name = "none"
    description = "Direct LLM call without additional reasoning"

    def run(self, prompt: str, context: dict | None = None) -> str:
        return self._call_llm(prompt)
