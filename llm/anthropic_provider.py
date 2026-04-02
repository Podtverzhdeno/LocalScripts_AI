"""Anthropic provider — Claude models via langchain-anthropic."""
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel


def make_anthropic_llm(model: str, temperature: float = 0.2) -> BaseChatModel:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set.\n"
            "  Add it to .env:  ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Get it at:       https://console.anthropic.com/"
        )
    return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
