"""
CheckpointAgent — manages user approval checkpoints after validation.
Handles code review, change requests, and alternative generation.
"""

import logging
from typing import Optional, Tuple
from agents.base import BaseAgent

logger = logging.getLogger("localscript.agents")


class CheckpointAgent(BaseAgent):
    """
    Manages checkpoint approval flow after successful validation.

    Actions:
    - Present code for user review
    - Handle approval/rejection
    - Generate alternative implementations
    - Save approved code to knowledge base
    """

    def __init__(self, llm):
        super().__init__("checkpoint", llm)

    def should_checkpoint(self, iteration: int, validation_passed: bool) -> bool:
        """
        Decide if checkpoint is needed.

        Args:
            iteration: Current iteration number
            validation_passed: Whether validation passed

        Returns:
            True if checkpoint should be triggered
        """
        # Checkpoint after first successful validation
        if iteration == 1 and validation_passed:
            return True

        # Checkpoint after any successful validation (user can review each attempt)
        return validation_passed

    def prepare_checkpoint_data(self, state: dict) -> dict:
        """
        Prepare data for checkpoint UI.

        Args:
            state: Current AgentState

        Returns:
            Dict with checkpoint information for frontend
        """
        return {
            "code": state.get("code"),
            "task": state.get("task"),
            "iteration": state.get("iterations"),
            "validation_status": "passed",
            "test_results": state.get("test_results"),
            "profile_metrics": state.get("profile_metrics"),
            "rag_used": state.get("approved_template") is not None,
        }

    def generate_alternatives(self, task: str, current_code: str, count: int = 2) -> list:
        """
        Generate alternative implementations with different approaches.

        Args:
            task: Original task
            current_code: Current implementation
            count: Number of alternatives to generate (default: 2)

        Returns:
            List of alternative code implementations
        """
        prompt = f"""Task: {task}

Current implementation exists. Generate {count} ALTERNATIVE approaches.

Current approach: [analyze the code below]
{current_code[:500]}...

Generate {count} different implementations:
1. Different algorithm/pattern
2. Different data structure
3. Different optimization strategy

For each alternative:
- Must solve the same task
- Must be significantly different from current
- Must be complete and runnable
- Return ONLY Lua code, no explanations

Alternative 1:
```lua"""

        try:
            response = self.invoke(prompt)
            # Parse multiple code blocks
            alternatives = self._extract_code_blocks(response)

            # Limit to requested count
            alternatives = alternatives[:count]

            logger.info(f"[Checkpoint] Generated {len(alternatives)} alternative(s)")
            return alternatives

        except Exception as e:
            logger.error(f"[Checkpoint] Failed to generate alternatives: {e}")
            return []

    def _extract_code_blocks(self, response: str) -> list:
        """
        Extract multiple code blocks from response.
        """
        import re

        # Match ```lua ... ``` or ``` ... ``` blocks
        pattern = r"```(?:lua)?\s*\n(.*?)\n?```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return [m.strip() for m in matches if m.strip()]

        # Fallback: split by common separators
        parts = response.split("Alternative")
        codes = []
        for part in parts[1:]:  # Skip first part (before "Alternative 1")
            # Extract code after colon or newline
            lines = part.split("\n")
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith("--") or line.strip().startswith("local") or line.strip().startswith("function"):
                    in_code = True
                if in_code:
                    code_lines.append(line)
            if code_lines:
                codes.append("\n".join(code_lines).strip())

        return codes[:2]  # Max 2 alternatives

    def process_user_feedback(self, feedback: str, task: str) -> str:
        """
        Process user's change request and enrich task.

        Args:
            feedback: User's feedback/change request
            task: Original task

        Returns:
            Enriched task with feedback incorporated
        """
        enriched = f"{task}\n\nUser feedback:\n{feedback}"
        logger.info(f"[Checkpoint] Processed user feedback: {feedback[:50]}...")
        return enriched

    def prepare_for_knowledge_base(self, state: dict) -> dict:
        """
        Prepare approved code for saving to RAG knowledge base.

        Args:
            state: Current AgentState with approved code

        Returns:
            Dict with metadata for RAG storage
        """
        # Extract key information
        task = state.get("task", "")
        code = state.get("code", "")
        test_results = state.get("test_results", {})
        profile_metrics = state.get("profile_metrics", {})

        # Generate tags from task (simple keyword extraction)
        tags = self._extract_tags(task, code)

        return {
            "code": code,
            "task": task,
            "tags": tags,
            "user_approved": True,
            "test_results": test_results,
            "profile_metrics": profile_metrics,
            "quality_score": self._calculate_quality_score(test_results, profile_metrics),
        }

    def _extract_tags(self, task: str, code: str) -> list:
        """
        Extract relevant tags from task and code.
        Simple keyword-based extraction for 7B models.
        """
        keywords = {
            "recursion": ["recursive", "recursion", "fibonacci", "factorial"],
            "memoization": ["memoization", "memo", "cache", "caching"],
            "sorting": ["sort", "quicksort", "mergesort", "bubblesort"],
            "searching": ["search", "binary search", "find", "lookup"],
            "dynamic-programming": ["dynamic", "dp", "memoization"],
            "data-structures": ["table", "stack", "queue", "tree", "graph"],
            "string-processing": ["string", "parse", "format", "match"],
            "validation": ["validate", "check", "verify"],
            "authentication": ["auth", "login", "password", "token"],
            "algorithms": ["algorithm", "pattern", "technique"],
        }

        tags = []
        text = (task + " " + code).lower()

        for tag, patterns in keywords.items():
            if any(pattern in text for pattern in patterns):
                tags.append(tag)

        return tags[:5]  # Max 5 tags

    def _calculate_quality_score(self, test_results: dict, profile_metrics: dict) -> float:
        """
        Calculate quality score (0.0 - 1.0) based on tests and performance.
        """
        score = 0.0

        # Test results (60% weight)
        if test_results:
            total = test_results.get("total", 0)
            passed = test_results.get("passed", 0)
            if total > 0:
                score += (passed / total) * 0.6

        # Performance (40% weight)
        if profile_metrics:
            exec_time = profile_metrics.get("time", 0)
            # Fast execution (< 0.1s) = full score
            if exec_time < 0.1:
                score += 0.4
            elif exec_time < 1.0:
                score += 0.3
            else:
                score += 0.2

        return min(score, 1.0)
