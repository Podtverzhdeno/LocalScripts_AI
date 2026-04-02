"""
BaseAgent — shared logic for all LocalScript agents.
Implements ChatDev-inspired <INFO> Finished stop signal pattern.
"""

import re

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from config.loader import get_agent_prompt


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

    def invoke(self, user_message: str) -> str:
        """Send a message to the LLM with the agent's system prompt."""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message),
        ]
        response = self.llm.invoke(messages)
        return response.content.strip()

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
