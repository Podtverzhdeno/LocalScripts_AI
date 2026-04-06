"""
Reviewer Agent — code quality review after successful validation.
Uses ChatDev's <INFO> Finished stop signal pattern.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel


class ReviewerAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("reviewer", llm)

    def review(self, code: str, task: str, profile_metrics: dict | None = None) -> tuple[bool, str]:
        """
        Review validated Lua code with optional performance metrics.
        Returns: (is_done, feedback)
        is_done=True means code is good (<INFO> Finished signal)
        """
        prompt = f"Task: {task}\n\nLua code to review:\n{code}\n"

        if profile_metrics:
            exec_time = profile_metrics.get("time", 0)
            memory = profile_metrics.get("memory", 0)
            prompt += f"\nPerformance metrics:\n- Execution time: {exec_time:.3f}s\n- Memory used: {memory}KB\n"
            prompt += "\nCheck if performance is acceptable for this task. "
            prompt += "Simple tasks (loops, math) should be <0.1s. Reject if unreasonably slow.\n"

        prompt += "\nProvide your review:"

        feedback = self.invoke(prompt)
        return self.is_finished(feedback), feedback
