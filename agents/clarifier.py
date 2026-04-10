"""
ClarifierAgent — analyzes task ambiguity and generates clarification questions.
Optimized for 7B models with minimal prompt overhead.
"""

import json
import logging
from typing import Optional
from agents.base import BaseAgent

logger = logging.getLogger("localscript.agents")


class ClarifierAgent(BaseAgent):
    """
    Analyzes user tasks for ambiguities and generates clarification questions.

    Designed for 7B models:
    - Short, focused prompts
    - Simple JSON output
    - Max 3 questions per task
    """

    def __init__(self, llm):
        super().__init__("clarifier", llm)

    def analyze_task(self, task: str) -> Optional[list]:
        """
        Analyze task for ambiguities and return clarification questions.

        Args:
            task: User's task description

        Returns:
            List of questions or None if task is clear:
            [
                {
                    "question": "What type of authentication?",
                    "options": ["JWT tokens", "Session cookies", "Basic Auth"],
                    "required": true
                }
            ]
        """
        # For simple/clear tasks, skip clarification
        if self._is_task_clear(task):
            logger.info("[Clarifier] Task is clear, no questions needed")
            return None

        prompt = f"""Task: {task}

Is this task clear or does it need clarification?

If CLEAR (specific requirements, no ambiguity):
Return: {{"clear": true}}

If UNCLEAR (missing details, multiple interpretations):
Return: {{"clear": false, "questions": [...]}}

Questions format (max 3):
{{
  "clear": false,
  "questions": [
    {{
      "question": "Short question?",
      "options": ["Option 1", "Option 2", "Option 3"],
      "required": true
    }}
  ]
}}

Rules:
- Only ask if truly ambiguous
- Max 3 questions
- Keep options short (2-4 words)
- Return ONLY JSON, no explanations

JSON:"""

        try:
            response = self.invoke(prompt)
            result = self._parse_json_response(response)

            if result.get("clear", False):
                logger.info("[Clarifier] Task is clear")
                return None

            questions = result.get("questions", [])
            if not questions:
                return None

            # Limit to 3 questions for 7B models
            questions = questions[:3]

            logger.info(f"[Clarifier] Generated {len(questions)} question(s)")
            return questions

        except Exception as e:
            logger.warning(f"[Clarifier] Failed to analyze task: {e}")
            return None

    def _is_task_clear(self, task: str) -> bool:
        """
        Quick heuristic check if task is clear enough.
        Avoids LLM call for obviously clear tasks.

        LowCode-specific: tasks with specific variable names or simple operations are clear.
        """
        task_lower = task.lower()

        # Clear indicators for LowCode tasks
        clear_indicators = [
            # Specific variable names mentioned
            "wf.vars.", "wf.initvariables",
            # Simple array operations
            "последний элемент", "первый элемент", "длина массива",
            "last element", "first element", "array length",
            # Simple math operations
            "увеличь", "уменьши", "increment", "decrement",
            "сумма", "sum", "count",
            # Simple string operations
            "объедини", "concatenate", "join",
            # Specific algorithms
            "fibonacci", "factorial", "quicksort", "binary search",
            "bubble sort", "merge sort", "prime numbers",
            "palindrome", "reverse string",
        ]

        # Ambiguous indicators: need clarification
        ambiguous_indicators = [
            # Vague data references without structure
            "данные", "data", "информация", "information",
            "объект", "object", "структура", "structure",
            # Vague operations
            "обработай", "process", "преобразуй", "transform",
            "очисти", "clean", "удали", "remove",
            # System-level terms
            "система", "system", "приложение", "application",
            "сервис", "service", "api", "crud",
            "парсер", "parser", "валидатор", "validator",
        ]

        # If task contains clear indicator, skip clarification
        if any(indicator in task_lower for indicator in clear_indicators):
            return True

        # If task mentions specific variable names (try_count_n, emails, etc.), it's clear
        if any(char.isdigit() or char == '_' for char in task) and 'wf' not in task_lower:
            # Has variable-like names (e.g., "try_count_n", "user_id")
            return True

        # If task is very short (<5 words) and vague, needs clarification
        if len(task.split()) < 5 and any(indicator in task_lower for indicator in ambiguous_indicators):
            return False

        # If task is detailed (>15 words), likely clear
        if len(task.split()) > 15:
            return True

        # Default: let LLM decide
        return False

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response, handling markdown fences.
        """
        # Remove markdown code fences if present
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            # Remove first and last lines (fences)
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response

        # Remove "json" language identifier
        response = response.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"[Clarifier] JSON parse error: {e}")
            logger.error(f"[Clarifier] Response: {response[:200]}")
            return {"clear": True}  # Fallback: assume clear

    def enrich_task_with_answers(self, task: str, questions: list, answers: dict) -> str:
        """
        Enrich original task with user answers.

        Args:
            task: Original task
            questions: List of questions asked
            answers: Dict mapping question index to answer

        Returns:
            Enriched task description with LowCode context
        """
        enrichments = []

        for i, question in enumerate(questions):
            answer = answers.get(str(i))
            if answer:
                # Format: "Question: Answer"
                q_text = question["question"].rstrip("?")
                enrichments.append(f"{q_text}: {answer}")

        if not enrichments:
            return task

        # Append clarifications to task with LowCode context
        enriched = f"{task}\n\nКонтекст LowCode:\n" + "\n".join(f"- {e}" for e in enrichments)

        # Add reminder about wf.vars if not already mentioned
        if "wf.vars" not in enriched.lower():
            enriched += "\n\nВажно: используй wf.vars для доступа к переменным"

        logger.info(f"[Clarifier] Enriched task with {len(enrichments)} answer(s)")

        return enriched
