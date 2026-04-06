"""
Validator Agent — runs luac + lua, explains errors if any.
This is what makes LocalScript different from ChatDev: real code execution.
"""

from agents.base import BaseAgent
from tools.lua_runner import LuaRunner, LuaResult
from langchain_core.language_models import BaseChatModel


class ValidatorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, runner: LuaRunner):
        super().__init__("validator", llm)
        self.runner = runner
        self._last_result: LuaResult | None = None  # Store last execution result

    def validate(self, code: str, task: str, iteration: int) -> tuple[bool, str]:
        """
        Run luac + lua. If errors, use LLM to explain them clearly.
        Returns: (is_valid, error_explanation_or_empty)
        """
        result: LuaResult = self.runner.execute(code, iteration)
        self._last_result = result  # Save for profiling metrics

        if result.success:
            return True, ""

        # Use LLM to explain errors (like ChatDev's Programmer Test Error Summary)
        explanation = self.invoke(
            f"Task: {task}\n\nLua code:\n{code}\n\nError output:\n{result.errors}\n\nExplain what is wrong:"
        )
        return False, explanation
