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

        prompt = f"""You are evaluating code examples for relevance.

TASK: {task}

RETRIEVED EXAMPLES:
{retrieved_examples}

INSTRUCTIONS:
Evaluate if these examples are relevant for the task.
Return ONLY a JSON object, nothing else.

RESPONSE FORMAT (copy this structure exactly):
{{"approved": false, "reason": "not relevant", "selected_examples": [], "confidence": 0.5}}

RULES:
- Set "approved" to true only if examples are highly relevant
- Set "approved" to false if examples are not relevant or task is different
- "selected_examples" is a list of numbers (1, 2, 3, etc.) - which examples to use
- "confidence" is a number between 0.0 and 1.0
- "reason" is a short explanation (max 10 words)

IMPORTANT: Return ONLY the JSON object. No markdown, no explanations, no code blocks.

JSON:"""

        try:
            # Timeout optimized for 7B models (60 seconds - prevents hanging while allowing completion)
            logger.info("[Approver] Starting evaluation...")
            response = self.invoke(prompt, timeout=60.0)
            logger.info(f"[Approver] LLM response received ({len(response)} chars)")

            # Try to parse JSON response
            # Remove markdown code fences if present
            response = response.strip()
            if response.startswith("```"):
                response = self.strip_code_fences(response)

            # Try to extract JSON from response if it contains extra text
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                response = response[start:end]

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

        except TimeoutError as e:
            logger.error(f"[Approver] Evaluation timed out after 30s")
            # Fallback: reject on timeout
            return {
                "approved": False,
                "reason": "Evaluation timed out, generating from scratch",
                "selected_examples": [],
                "confidence": 0.0
            }
        except json.JSONDecodeError as e:
            logger.error(f"[Approver] Failed to parse JSON response: {e}")
            logger.error(f"[Approver] Raw response: {response[:500]}")
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
