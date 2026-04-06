"""
Evolver Agent — finds improvements and triggers evolution cycles.
Analyzes project metrics and suggests optimizations.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from pathlib import Path
import json


class EvolverAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("evolver", llm)

    def analyze(self, manifest: dict, metrics: dict) -> dict:
        """
        Analyze project and find improvement opportunities.
        Returns: {
            "improvements": [
                {
                    "file": "db.lua",
                    "issue": "Slow performance (0.5s)",
                    "suggestion": "Add caching for frequent queries"
                }
            ],
            "priority": "high" | "medium" | "low",
            "should_evolve": True | False
        }
        """
        # TODO: Use LLM to analyze code and metrics
        # For now, simple heuristics

        improvements = []

        # Check performance metrics
        for file_info in manifest.get("files", []):
            file_name = file_info["path"]
            if file_name in metrics:
                exec_time = metrics[file_name].get("time", 0)
                if exec_time > 0.1:
                    improvements.append({
                        "file": file_name,
                        "issue": f"Slow execution ({exec_time:.3f}s)",
                        "suggestion": "Consider optimization or caching"
                    })

        # Check code complexity
        for file_info in manifest.get("files", []):
            if file_info["lines"] > 200:
                improvements.append({
                    "file": file_info["path"],
                    "issue": f"Large file ({file_info['lines']} lines)",
                    "suggestion": "Consider splitting into smaller modules"
                })

        return {
            "improvements": improvements,
            "priority": "high" if len(improvements) > 2 else "medium" if improvements else "low",
            "should_evolve": len(improvements) > 0
        }

    def select_task(self, improvements: list[dict]) -> dict | None:
        """Select the most important improvement task."""
        if not improvements:
            return None

        # For now, just return the first one
        # TODO: Use LLM to prioritize
        return improvements[0]
