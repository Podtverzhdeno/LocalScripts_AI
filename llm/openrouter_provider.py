"""
OpenRouter provider — OpenAI-compatible API with access to many models.
Uses sk-or-v1-... keys from https://openrouter.ai/
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


def make_openrouter_llm(model: str, temperature: float = 0.2) -> BaseChatModel:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY not set.\n"
            "  Add it to .env:  OPENROUTER_API_KEY=sk-or-v1-...\n"
            "  Get it at:       https://openrouter.ai/keys"
        )
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/localscript",
            "X-Title": "LocalScript",
        },
    )
