"""
Generator Agent — writes Lua code.
On retry: receives previous errors and fixes them (like ChatDev's Programmer + error context).
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel


class GeneratorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("generator", llm)

    def generate(self, task: str, errors: str | None = None, review: str | None = None) -> str:
        """Generate or fix Lua code based on task + optional feedback."""
        parts = [f"Task: {task}"]

        if errors:
            parts.append(f"\nPrevious code had errors:\n{errors}\n\nFix these errors.")
        if review:
            parts.append(f"\nReviewer feedback:\n{review}\n\nApply these improvements.")

        parts.append("\nWrite the Lua code now:")
        prompt = "\n".join(parts)
        # Use reasoning strategy on first generation (no errors/review = fresh task).
        # On retries (errors or review present), use direct invoke to avoid
        # re-running the full strategy on a fix — the fix prompt is already focused.
        if errors or review:
            raw = self.invoke(prompt)
        else:
            raw = self.invoke_with_strategy(prompt)
        # LLMs often wrap code in ```lua ... ``` despite prompt instructions — strip it
        return self.strip_code_fences(raw)
