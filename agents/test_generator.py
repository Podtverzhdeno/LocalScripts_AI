"""
Test Generator Agent — generates functional test cases from task description.

This is what Aleksandr Bordash requested:
"Надо написать test case, который скажет: вот у email такой-то, вот это email или нет"

NOT unit tests, but functional test cases that verify business logic.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
import logging

logger = logging.getLogger("localscript.agents")


class TestGeneratorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel):
        super().__init__("test_generator", llm)

    def generate_tests(self, task: str, code: str) -> str:
        """
        Generate functional test cases based on task description.
        Returns Lua code with test assertions.

        Example output:
        ```lua
        -- Test case 1: valid email
        assert(validate_email("test@example.com") == true, "Should accept valid email")

        -- Test case 2: invalid email
        assert(validate_email("invalid") == false, "Should reject invalid email")
        ```
        """
        logger.info(f"[TestGenerator] Starting test generation (task: {len(task)} chars, code: {len(code)} chars)")

        prompt = f"""Task: {task}

Generated code:
{code}

Generate functional test cases for this code. Follow these rules:

1. Create 5-10 test cases that verify the business logic
2. Use Lua assert() statements with descriptive messages
3. Cover:
   - Normal/valid inputs (happy path)
   - Invalid inputs (edge cases)
   - Boundary conditions
   - Error cases

4. Format:
   -- Test case N: description
   assert(function_call(input) == expected_output, "Error message")

5. Return ONLY Lua test code, no explanations
6. Tests should be executable and demonstrate the code works

Example for email validator:
-- Test 1: valid email
assert(validate_email("user@example.com") == true, "Valid email should pass")

-- Test 2: missing @
assert(validate_email("invalid.email") == false, "Email without @ should fail")

Generate tests now:"""

        logger.info("[TestGenerator] Invoking LLM for test generation...")
        raw = self.invoke(prompt)

        logger.info(f"[TestGenerator] LLM response received ({len(raw)} chars)")
        logger.info("[TestGenerator] Stripping markdown fences...")

        # Strip markdown fences that LLM might add
        cleaned = self.strip_code_fences(raw)

        logger.info(f"[TestGenerator] Test generation complete ({len(cleaned)} chars, ~{cleaned.count('assert')} assertions)")
        return cleaned
