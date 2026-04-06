"""
Decomposer Agent — analyzes generated code and creates metadata.
Creates manifest.json with file structure, dependencies, and metrics.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from pathlib import Path
import json


class DecomposerAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("decomposer", llm)

    def analyze(self, project_dir: Path, files: list[str]) -> dict:
        """
        Analyze generated files and create manifest.
        Returns: {
            "files": [
                {
                    "path": "auth.lua",
                    "functions": ["login", "logout"],
                    "dependencies": ["db.lua"],
                    "lines": 45,
                    "complexity": "medium"
                }
            ],
            "total_lines": 150,
            "total_files": 4
        }
        """
        manifest = {
            "files": [],
            "total_lines": 0,
            "total_files": len(files)
        }

        for file_name in files:
            file_path = project_dir / "src" / file_name
            if not file_path.exists():
                continue

            code = file_path.read_text(encoding="utf-8")
            lines = len(code.splitlines())

            # TODO: Use LLM to extract functions and dependencies
            # For now, simple analysis
            file_info = {
                "path": file_name,
                "functions": [],  # TODO: extract from code
                "dependencies": [],  # TODO: parse require() calls
                "lines": lines,
                "complexity": "medium"  # TODO: calculate
            }

            manifest["files"].append(file_info)
            manifest["total_lines"] += lines

        return manifest

    def create_readme(self, project_dir: Path, plan: dict, manifest: dict) -> None:
        """Generate README.md for the project."""
        readme = f"""# Project

## Architecture
{plan.get('structure', 'N/A')}

## Files
"""
        for file_info in manifest["files"]:
            readme += f"- **{file_info['path']}** ({file_info['lines']} lines)\n"
            if file_info['dependencies']:
                readme += f"  - Dependencies: {', '.join(file_info['dependencies'])}\n"

        readme += f"\n## Statistics\n"
        readme += f"- Total files: {manifest['total_files']}\n"
        readme += f"- Total lines: {manifest['total_lines']}\n"

        (project_dir / "README.md").write_text(readme, encoding="utf-8")
