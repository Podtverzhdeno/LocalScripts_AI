"""
Reviewer Agent — code quality review after successful validation.
Uses ChatDev's <INFO> Finished stop signal pattern.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel


class ReviewerAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("reviewer", llm)

    def review(self, code: str, task: str) -> tuple[bool, str]:
        """
        Review validated Lua code.
        Returns: (is_done, feedback)
        is_done=True means code is good (<INFO> Finished signal)
        """
        feedback = self.invoke(
            f"Task: {task}\n\nLua code to review:\n{code}\n\nProvide your review:"
        )
        return self.is_finished(feedback), feedback
