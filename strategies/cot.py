"""
Chain-of-Thought (CoT) strategy — think step-by-step, then produce code.

The LLM first reasons about the problem (algorithm, edge cases, data structures),
then generates code based on its own reasoning. 2 LLM calls total.

Particularly effective for algorithmic tasks where planning matters.
"""

import logging

from strategies.base import ReasoningStrategy

logger = logging.getLogger("localscript.strategies.cot")

_REASONING_SYSTEM = (
    "You are a senior software architect. Analyze the task below and produce "
    "a step-by-step plan BEFORE writing any code. Cover:\n"
    "1. Algorithm choice and why\n"
    "2. Key data structures\n"
    "3. Edge cases to handle\n"
    "4. Expected output format\n\n"
    "Be concise — max 200 words. Do NOT write code yet."
)

_CODE_SYSTEM = (
    "You are an expert programmer. Using the reasoning plan below, "
    "write the code. Return ONLY code — no explanations, no markdown fences."
)


class ChainOfThoughtStrategy(ReasoningStrategy):
    """
    Chain-of-Thought: reason first, then code.

    Cost: 2 LLM calls per invocation.
    Best for: algorithmic tasks, complex logic, multi-step problems.
    """

    name = "cot"
    description = "Reason step-by-step, then generate code (2 LLM calls)"

    def run(self, prompt: str, context: dict | None = None) -> str:
        # Step 1: Reason about the problem
        logger.info("[cot] Step 1/2: reasoning about the problem")
        reasoning = self._call_llm(prompt, system=_REASONING_SYSTEM)

        # Step 2: Generate code based on reasoning
        logger.info("[cot] Step 2/2: generating code from plan")
        code_prompt = (
            f"Task: {prompt}\n\n"
            f"Your reasoning plan:\n{reasoning}\n\n"
            f"Now write the code:"
        )
        code = self._call_llm(code_prompt, system=_CODE_SYSTEM)

        logger.info("[cot] Done — reasoning: %d chars, code: %d chars", len(reasoning), len(code))
        return code
