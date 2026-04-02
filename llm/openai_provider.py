"""OpenAI provider — thin wrapper used by factory.py."""
import os
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


def make_openai_llm(model: str, temperature: float = 0.2) -> BaseChatModel:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set.\n"
            "  Add it to .env:  OPENAI_API_KEY=sk-...\n"
            "  Or export it:    export OPENAI_API_KEY=sk-..."
        )
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
