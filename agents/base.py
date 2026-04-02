"""
BaseAgent — shared logic for all LocalScript agents.
Implements ChatDev-inspired <INFO> Finished stop signal pattern.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from config.loader import get_agent_prompt


STOP_SIGNAL = "<INFO> Finished"


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

    def is_finished(self, response: str) -> bool:
        """Check for ChatDev-style stop signal in response."""
        return STOP_SIGNAL in response
