"""
Architect Agent — plans project structure from requirements.
Analyzes task/spec and creates a project plan with file structure and dependencies.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel


class ArchitectAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("architect", llm)

    def plan(self, requirements: str) -> dict:
        """
        Analyze requirements and create project plan.
        Returns: {
            "files": [
                {"name": "auth.lua", "purpose": "...", "dependencies": [...]},
                ...
            ],
            "structure": "description of overall architecture",
            "order": ["config.lua", "db.lua", "auth.lua", "api.lua"]
        }
        """
        prompt = f"""You are a software architect planning a Lua project.

Requirements:
{requirements}

Create a project plan with:
1. List of files needed (name, purpose, dependencies)
2. Overall architecture description
3. Build order (which files to create first)

Output format (JSON):
{{
  "files": [
    {{"name": "config.lua", "purpose": "Configuration settings", "dependencies": []}},
    {{"name": "db.lua", "purpose": "Database operations", "dependencies": ["config.lua"]}},
    {{"name": "auth.lua", "purpose": "Authentication logic", "dependencies": ["db.lua", "crypto.lua"]}}
  ],
  "structure": "Modular architecture with separate concerns...",
  "order": ["config.lua", "db.lua", "crypto.lua", "auth.lua", "api.lua"]
}}

Keep it simple - 3-7 files maximum. Focus on core functionality.
"""

        response = self.invoke(prompt)

        # Parse JSON from response
        import json
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError(f"Could not parse JSON from architect response: {response}")

        try:
            plan = json.loads(json_str)
            return plan
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from architect: {e}\n{json_str}")
