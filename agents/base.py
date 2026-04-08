"""
BaseAgent — shared logic for all LocalScript agents.
Implements ChatDev-inspired <INFO> Finished stop signal pattern.
Supports optional reasoning strategies (reflect, cot) for enhanced output.
"""

import logging
import re
import threading
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from config.loader import get_agent_prompt, get_strategy_name

logger = logging.getLogger("localscript.agents")


STOP_SIGNAL = "<INFO> Finished"

# Matches ```lua ... ``` or ``` ... ``` blocks (greedy, DOTALL)
_CODE_FENCE_RE = re.compile(r"```(?:lua)?\s*\n(.*?)\n?```", re.DOTALL)


class BaseAgent:
    """
    Base class for all agents.
    - Loads system prompt from config/agents.yaml by role name
    - Wraps LLM calls with SystemMessage + HumanMessage
    - Implements is_finished() stop signal check (ChatDev pattern)
    """

    def __init__(self, role: str, llm: BaseChatModel):
        self.role = role
        self.llm = llm
        self.system_prompt = get_agent_prompt(role)

    def invoke(self, user_message: str, timeout: Optional[float] = None) -> str:
        """
        Send a message to the LLM with the agent's system prompt.

        Args:
            user_message: The message to send
            timeout: Optional timeout in seconds (cross-platform)

        Returns:
            LLM response content

        Raises:
            TimeoutError: If timeout is exceeded
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message),
        ]

        if timeout is None:
            response = self.llm.invoke(messages)
            return response.content.strip()

        # Cross-platform timeout using threading
        result = {"response": None, "error": None}

        def _invoke():
            try:
                result["response"] = self.llm.invoke(messages)
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=_invoke, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            logger.warning(f"[{self.role}] LLM call timed out after {timeout}s")
            raise TimeoutError(f"LLM call timed out after {timeout} seconds")

        if result["error"]:
            raise result["error"]

        return result["response"].content.strip()

    def invoke_with_strategy(self, user_message: str) -> str:
        """
        Send a message through the configured reasoning strategy.

        If strategy is "none" (default), behaves identically to invoke().
        Otherwise, the strategy wraps the LLM call with multi-step reasoning.
        """
        strategy_name = get_strategy_name(self.role)
        if strategy_name == "none":
            return self.invoke(user_message)

        from strategies.registry import get_strategy
        strategy = get_strategy(strategy_name, self.llm)
        logger.info("[%s] Using strategy: %s", self.role, strategy_name)
        return strategy.run(user_message, context={"role": self.role})

    @staticmethod
    def strip_code_fences(text: str) -> str:
        """
        Remove markdown code fences (```lua ... ```) that LLMs add despite instructions.
        If the entire response is wrapped in a single fence block, extract its content.
        If multiple blocks exist, concatenate their contents.
        If no fences found, return text as-is.
        """
        matches = _CODE_FENCE_RE.findall(text)
        if matches:
            return "\n\n".join(m.strip() for m in matches)
        # Fallback: strip leading/trailing ``` lines even without proper block structure
        lines = text.splitlines()
        while lines and lines[0].strip().startswith("```"):
            lines.pop(0)
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        return "\n".join(lines).strip()

    def is_finished(self, response: str) -> bool:
        """Check for ChatDev-style stop signal in response."""
        return STOP_SIGNAL in response
