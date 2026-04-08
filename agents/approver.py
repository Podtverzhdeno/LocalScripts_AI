"""
Approver Agent — evaluates relevance of retrieved RAG examples.
Decides whether the retrieved examples are relevant enough to use as templates,
or if generation should start from scratch.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from typing import List, Tuple, Dict
import logging
import json

logger = logging.getLogger("localscript.agents")


class ApproverAgent(BaseAgent):
    """
    Agent responsible for evaluating RAG retrieval results.

    This agent:
    1. Reviews retrieved examples from RAG
    2. Evaluates their relevance to the user's task
    3. Decides: APPROVE (use as template) or REJECT (generate from scratch)
    4. If approved, selects the best example(s) to use
    """

    def __init__(self, llm: BaseChatModel):
        super().__init__("approver", llm)

    def evaluate(
        self,
        task: str,
        retrieved_examples: str,
        min_score_threshold: float = 0.5
    ) -> Dict:
        """
        Evaluate whether retrieved examples are relevant for the task.

        Args:
            task: User's task description
            retrieved_examples: Formatted string with retrieved examples
            min_score_threshold: Minimum relevance score to consider approval

        Returns:
            Dict with:
                - approved: bool (True if examples should be used)
                - reason: str (explanation of decision)
                - selected_examples: List[int] (indices of examples to use, 1-based)
                - confidence: float (0-1, confidence in decision)
        """
        if not retrieved_examples or "No examples found" in retrieved_examples:
            logger.info("[Approver] No examples to evaluate")
            return {
                "approved": False,
                "reason": "No examples found in knowledge base",
                "selected_examples": [],
                "confidence": 1.0
            }

        prompt = f"""Task: {task}

{retrieved_examples}

Evaluate whether these retrieved examples are relevant and useful for the given task.

Consider:
1. Do the examples demonstrate similar algorithms, patterns, or techniques needed for the task?
2. Are the examples close enough to serve as a template or starting point?
3. Would using these examples improve code quality compared to generating from scratch?

CRITICAL: Return ONLY valid JSON, no explanations, no markdown.

Output format:
{{
  "approved": true/false,
  "reason": "Brief explanation (1-2 sentences)",
  "selected_examples": [1, 2],
  "confidence": 0.85
}}

Rules:
- approved: true if examples are relevant and should be used as templates
- approved: false if examples are not relevant or task is too different
- selected_examples: list of example numbers (1-based) to use (empty if not approved)
- confidence: 0.0-1.0, how confident you are in this decision
- reason: explain why you approved or rejected

Respond with JSON only:"""

        try:
            response = self.invoke(prompt)

            # Try to parse JSON response
            # Remove markdown code fences if present
            response = response.strip()
            if response.startswith("```"):
                response = self.strip_code_fences(response)

            result = json.loads(response)

            # Validate structure
            if not all(k in result for k in ["approved", "reason", "selected_examples", "confidence"]):
                raise ValueError("Missing required fields in response")

            logger.info(f"[Approver] Decision: {'APPROVED' if result['approved'] else 'REJECTED'}")
            logger.info(f"[Approver] Reason: {result['reason']}")
            logger.info(f"[Approver] Confidence: {result['confidence']:.2f}")

            if result['approved'] and result['selected_examples']:
                logger.info(f"[Approver] Selected examples: {result['selected_examples']}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"[Approver] Failed to parse JSON response: {e}")
            logger.error(f"[Approver] Raw response: {response[:200]}")
            # Fallback: reject if we can't parse
            return {
                "approved": False,
                "reason": "Failed to evaluate examples (JSON parse error)",
                "selected_examples": [],
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"[Approver] Evaluation failed: {e}")
            return {
                "approved": False,
                "reason": f"Evaluation error: {str(e)}",
                "selected_examples": [],
                "confidence": 0.0
            }

    def extract_approved_examples(
        self,
        results: List[Tuple[any, float]],
        selected_indices: List[int]
    ) -> List[Tuple[any, float]]:
        """
        Extract only the approved examples from results.

        Args:
            results: Original list of (document, score) tuples
            selected_indices: List of 1-based indices to extract

        Returns:
            Filtered list of (document, score) tuples
        """
        approved = []
        for idx in selected_indices:
            if 1 <= idx <= len(results):
                approved.append(results[idx - 1])  # Convert to 0-based
            else:
                logger.warning(f"[Approver] Invalid index {idx}, skipping")

        return approved
