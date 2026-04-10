"""
Architect Agent — plans project structure from requirements.
Analyzes task/spec and creates a project plan with file structure and dependencies.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from utils.parsing import parse_json_robust
from schemas import ProjectPlan


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

        # Use robust JSON parsing with Pydantic validation
        try:
            plan = parse_json_robust(
                response,
                schema=ProjectPlan,
                llm=self.llm,
                fallback_to_minimal=True
            )

            # Convert Pydantic model to dict for backward compatibility
            if hasattr(plan, 'model_dump'):
                return plan.model_dump()
            elif hasattr(plan, 'dict'):
                return plan.dict()
            else:
                return plan

        except Exception as e:
            print(f"[Architect] Failed to parse response. Error: {e}")
            print(f"[Architect] Response was:\n{response[:500]}...")
            raise ValueError(f"Invalid response from architect: {e}\nResponse: {response[:200]}")
