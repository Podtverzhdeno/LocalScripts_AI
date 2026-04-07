"""
IntegratorAgent — tests integration between modules.
Creates main.lua that loads all modules and verifies they work together.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from tools.lua_runner import LuaRunner
from pathlib import Path


class IntegratorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, runner: LuaRunner):
        super().__init__("integrator", llm)
        self.runner = runner

    def test_integration(
        self,
        files: dict[str, str],
        plan: dict,
        project_dir: Path
    ) -> dict:
        """
        Test that all files work together.

        Args:
            files: {filename: code}
            plan: Project plan from Architect
            project_dir: Project directory path

        Returns:
            {
                "success": True/False,
                "issues": [
                    {"file": "auth.lua", "problem": "calls db.connect() but function not found"}
                ],
                "output": "execution output",
                "main_code": "generated main.lua code"
            }
        """
        print("\n[Integrator] Testing integration...")

        # Generate main.lua that loads and tests all modules
        main_code = self._generate_main(files, plan)

        # Save main.lua temporarily
        main_path = project_dir / "src" / "main.lua"
        main_path.write_text(main_code, encoding="utf-8")

        # Execute main.lua
        result = self.runner.execute(main_code, iteration=0)

        if result.success:
            print("[Integrator] ✓ All modules integrated successfully")
            return {
                "success": True,
                "issues": [],
                "output": result.stdout,
                "main_code": main_code
            }

        # Analyze integration errors
        print(f"[Integrator] ✗ Integration failed")
        issues = self._analyze_errors(result.errors, files, plan)

        return {
            "success": False,
            "issues": issues,
            "output": result.stdout + "\n" + result.stderr,
            "main_code": main_code
        }

    def _generate_main(self, files: dict[str, str], plan: dict) -> str:
        """Generate main.lua that loads and tests all modules."""
        prompt = f"""Generate a main.lua file that:
1. Loads all project modules in dependency order
2. Calls key functions from each module to verify they work
3. Prints success messages for each module

Project structure:
Files: {list(files.keys())}
Build order: {plan.get('order', [])}

Available code:
{self._format_files_summary(files)}

Output ONLY Lua code for main.lua. No markdown, no explanations.
The code should:
- Load modules in correct order
- Call main functions with sample data
- Print "[Module] OK" for each successful module
- Use pcall() to catch errors gracefully
"""

        main_code = self.invoke(prompt)
        return self.strip_code_fences(main_code)

    def _format_files_summary(self, files: dict[str, str]) -> str:
        """Create summary of available functions in each file."""
        summary = []
        for filename, code in files.items():
            functions = self._extract_functions(code)
            if functions:
                summary.append(f"\n{filename}:")
                for func in functions[:5]:  # Limit to 5 functions
                    summary.append(f"  - {func}")
        return "\n".join(summary)

    def _extract_functions(self, code: str) -> list[str]:
        """Extract function signatures from Lua code."""
        import re
        pattern = r'(?:local\s+)?function\s+(\w+(?:\.\w+)?)\s*\(([^)]*)\)'
        matches = re.findall(pattern, code)
        return [f"{name}({params.strip()})" for name, params in matches]

    def _analyze_errors(self, errors: str, files: dict[str, str], plan: dict) -> list[dict]:
        """Analyze integration errors and identify issues."""
        prompt = f"""Analyze integration errors and identify specific issues.

Errors:
{errors}

Project files: {list(files.keys())}

For each error, identify:
1. Which file has the problem
2. What specifically is wrong (missing function, wrong API, etc.)
3. How to fix it

Output ONLY a JSON array:
[
  {{"file": "filename.lua", "problem": "specific issue", "fix": "how to fix"}}
]
"""

        response = self.invoke(prompt)

        # Parse JSON response
        try:
            import json
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")[1:-1]
                response = "\n".join(lines)
            issues = json.loads(response)
            return issues if isinstance(issues, list) else []
        except:
            # Fallback: return generic issue
            return [{
                "file": "unknown",
                "problem": errors[:200],
                "fix": "Check error messages and fix manually"
            }]
