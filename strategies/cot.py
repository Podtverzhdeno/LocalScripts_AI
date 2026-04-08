"""
Chain-of-Thought (CoT) strategy — optimized for 7B-12B local models.
"""
import logging
from strategies.base import ReasoningStrategy

logger = logging.getLogger("localscript.strategies.cot")

# Убираем roleplay, даём чёткие инструкции
_REASONING_SYSTEM = (
    "Analyze the programming task and create a concise implementation plan.\n"
    "Target language: Lua 5.3+\n"
    "Constraints: no external libraries, no require(), standalone execution\n\n"
    "Your plan MUST cover:\n"
    "1. Algorithm: which approach and why (one sentence)\n"
    "2. Data structures: what Lua tables/variables you will use\n"
    "3. Edge cases: nil inputs, empty tables, zero/negative numbers\n"
    "4. Function signatures: exact names and parameters\n\n"
    "Format your answer as numbered list. Max 150 words. NO CODE."
)

_CODE_SYSTEM = (
    "Write Lua 5.3 code based on the implementation plan.\n"
    "Rules:\n"
    "- Output ONLY raw Lua code\n"
    "- No markdown, no backticks, no comments explaining the plan\n"
    "- No require(), no external libraries\n"
    "- Handle all edge cases from the plan\n"
    "- Code must run standalone with lua interpreter"
)

# Адаптируем глубину reasoning под сложность задачи
_SIMPLE_KEYWORDS = {"fibonacci", "factorial", "sort", "reverse", "count", "sum", "max", "min"}

def _estimate_complexity(prompt: str) -> str:
    prompt_lower = prompt.lower()
    word_count = len(prompt.split())
    
    if word_count < 10 and any(kw in prompt_lower for kw in _SIMPLE_KEYWORDS):
        return "simple"
    elif word_count > 30 or any(kw in prompt_lower for kw in {"parser", "compiler", "tree", "graph", "cache", "concurrent"}):
        return "complex"
    return "medium"


class ChainOfThoughtStrategy(ReasoningStrategy):
    name = "cot"
    description = "Reason step-by-step, then generate code (2 LLM calls)"

    def run(self, prompt: str, context: dict | None = None) -> str:
        complexity = _estimate_complexity(prompt)
        logger.info("[cot] Estimated complexity: %s", complexity)

        # Step 1: Reasoning с явным word limit под сложность
        word_limit = {"simple": 80, "medium": 150, "complex": 250}[complexity]
        
        reasoning_prompt = (
            f"Task: {prompt}\n\n"
            f"Create implementation plan. Max {word_limit} words."
        )
        
        logger.info("[cot] Step 1/2: reasoning (limit=%d words)", word_limit)
        reasoning = self._call_llm(reasoning_prompt, system=_REASONING_SYSTEM)
        
        # Валидируем что reasoning не содержит код (малые модели часто нарушают инструкцию)
        if "```" in reasoning or reasoning.count("\n") > 20:
            logger.warning("[cot] Reasoning looks like code, truncating")
            # Берём только первые N строк
            reasoning = "\n".join(reasoning.split("\n")[:15])

        # Step 2: Code generation — вставляем reasoning как часть контекста задачи
        code_prompt = (
            f"Task: {prompt}\n\n"
            f"Implementation plan:\n{reasoning}\n\n"
            f"Write the Lua code now. Follow the plan exactly."
        )
        
        logger.info("[cot] Step 2/2: generating code")
        code = self._call_llm(code_prompt, system=_CODE_SYSTEM)
        
        logger.info(
            "[cot] Done — complexity=%s reasoning=%d chars code=%d chars",
            complexity, len(reasoning), len(code)
        )
        return code
