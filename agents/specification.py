"""
SpecificationAgent — creates detailed specifications for files.
Converts high-level descriptions into actionable specs with functions, API, data structures.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from utils.parsing import parse_json_robust
from schemas import FileSpecification
import json


class SpecificationAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("specification", llm)

    def create_spec(
        self,
        file_info: dict,
        plan: dict,
        existing_files: dict[str, str]
    ) -> dict:
        """
        Create detailed specification for a file.

        Args:
            file_info: {"name": "auth.lua", "purpose": "...", "dependencies": [...]}
            plan: Full project plan from Architect
            existing_files: Already generated files {filename: code}

        Returns:
            {
                "file": "auth.lua",
                "functions": [
                    {
                        "name": "login",
                        "params": ["username", "password"],
                        "returns": "bool, error_message",
                        "description": "Authenticates user credentials"
                    }
                ],
                "dependencies_api": {
                    "db.lua": ["connect()", "query(sql)", "close()"]
                },
                "data_structures": [
                    {"name": "User", "fields": ["id", "username", "password_hash"]}
                ],
                "edge_cases": ["empty username", "invalid password", "db connection failed"],
                "example_usage": "local ok, err = login('user', 'pass')"
            }
        """
        # Build context from existing files
        context = self._build_context(file_info, existing_files)

        prompt = f"""Create a detailed specification for {file_info['name']}.

Purpose: {file_info['purpose']}
Dependencies: {', '.join(file_info['dependencies']) if file_info['dependencies'] else 'none'}

{context}

Project structure:
{json.dumps(plan, indent=2)}

Output ONLY valid JSON with this structure:
{{
  "file": "{file_info['name']}",
  "functions": [
    {{"name": "function_name", "params": ["param1", "param2"], "returns": "return_type", "description": "what it does"}}
  ],
  "dependencies_api": {{
    "dependency.lua": ["available_function1()", "available_function2()"]
  }},
  "data_structures": [
    {{"name": "StructName", "fields": ["field1", "field2"]}}
  ],
  "edge_cases": ["case1", "case2"],
  "example_usage": "code example"
}}

Be specific and concrete. List actual function names, parameters, and return types.
"""

        response = self.invoke(prompt)

        # Use robust JSON parsing with Pydantic validation
        try:
            spec = parse_json_robust(
                response,
                schema=FileSpecification,
                llm=self.llm,
                fallback_to_minimal=True
            )

            # Convert Pydantic model to dict for backward compatibility
            if hasattr(spec, 'model_dump'):
                return spec.model_dump()
            elif hasattr(spec, 'dict'):
                return spec.dict()
            else:
                return spec

        except Exception as e:
            print(f"[SpecificationAgent] Warning: Failed to parse response: {e}")
            # Return minimal spec as fallback
            return {
                "file": file_info['name'],
                "functions": [],
                "dependencies_api": {},
                "data_structures": [],
                "edge_cases": [],
                "example_usage": ""
            }

    def _build_context(self, file_info: dict, existing_files: dict[str, str]) -> str:
        """Build context from dependency files."""
        if not file_info['dependencies']:
            return ""

        context_parts = ["Available APIs from dependencies:"]

        for dep in file_info['dependencies']:
            if dep in existing_files:
                code = existing_files[dep]
                # Extract function signatures
                functions = self._extract_functions(code)
                if functions:
                    context_parts.append(f"\nFrom {dep}:")
                    for func in functions:
                        context_parts.append(f"  - {func}")

        return "\n".join(context_parts) if len(context_parts) > 1 else ""

    def _extract_functions(self, code: str) -> list[str]:
        """Extract function signatures from Lua code."""
        import re

        # Match: function name(...) or local function name(...)
        pattern = r'(?:local\s+)?function\s+(\w+(?:\.\w+)?)\s*\(([^)]*)\)'
        matches = re.findall(pattern, code)

        functions = []
        for name, params in matches:
            params_clean = params.strip() if params.strip() else ""
            functions.append(f"{name}({params_clean})")

        return functions[:10]  # Limit to 10 functions
