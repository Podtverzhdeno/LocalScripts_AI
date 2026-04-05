"""
Reflect strategy — generate → self-critique → revise.

The LLM produces a draft, then critiques its own output,
then revises based on the critique. 3 LLM calls total.

Works well even on smaller models (8B+) because each step
has a clear, focused instruction.
"""

import logging

from strategies.base import ReasoningStrategy

logger = logging.getLogger("localscript.strategies.reflect")

# System prompts for each phase — kept short to minimize token overhead
_CRITIQUE_SYSTEM = (
    "You are a critical code reviewer. Find specific flaws, bugs, edge cases, "
    "and improvements in the code below. Be concise and actionable — "
    "list only real issues, not style preferences. Max 150 words."
)

_REVISE_SYSTEM = (
    "You are an expert programmer. Revise the code below based on the critique. "
    "Return ONLY the improved code — no explanations, no markdown fences."
)


class ReflectStrategy(ReasoningStrategy):
    """
    Self-reflection: draft → critique → revise.

    Cost: 3 LLM calls per invocation.
    Best for: code generation where self-review catches obvious bugs.
    """

    name = "reflect"
    description = "Generate → self-critique → revise (3 LLM calls)"

    def run(self, prompt: str, context: dict | None = None) -> str:
        # Step 1: Generate initial draft
        logger.info("[reflect] Step 1/3: generating draft")
        draft = self._call_llm(prompt)

        # Step 2: Self-critique
        logger.info("[reflect] Step 2/3: self-critique")
        critique_prompt = f"Code to review:\n{draft}\n\nOriginal task: {prompt}"
        critique = self._call_llm(critique_prompt, system=_CRITIQUE_SYSTEM)

        # Step 3: Revise based on critique
        logger.info("[reflect] Step 3/3: revising based on critique")
        revise_prompt = (
            f"Original task: {prompt}\n\n"
            f"Draft code:\n{draft}\n\n"
            f"Critique:\n{critique}\n\n"
            f"Write the improved code:"
        )
        revised = self._call_llm(revise_prompt, system=_REVISE_SYSTEM)

        logger.info("[reflect] Done — draft: %d chars → revised: %d chars", len(draft), len(revised))
        return revised
