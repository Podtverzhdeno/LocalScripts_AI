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

        # Parse JSON from response - handle multiple formats
        import json
        import re

        # Try 1: Extract from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try 2: Find JSON object directly (greedy match)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try 3: Entire response might be JSON
                json_str = response.strip()

        # Clean up common issues
        json_str = json_str.strip()

        # Remove trailing commas before closing brackets (invalid JSON)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        try:
            plan = json.loads(json_str)

            # Validate required fields
            if "files" not in plan or "order" not in plan:
                raise ValueError("Missing required fields: 'files' or 'order'")

            # Ensure structure field exists
            if "structure" not in plan:
                plan["structure"] = "Project structure"

            return plan

        except json.JSONDecodeError as e:
            # If parsing fails, log the response for debugging
            print(f"[Architect] Failed to parse JSON. Error: {e}")
            print(f"[Architect] Response was:\n{response[:500]}...")
            raise ValueError(f"Invalid JSON from architect: {e}\nResponse: {response[:200]}")
