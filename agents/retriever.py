"""
Retriever Agent — searches RAG knowledge base for relevant examples.
Specialized agent that focuses solely on finding the best matching code examples
from the vector database based on user task description.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("localscript.agents")


class RetrieverAgent(BaseAgent):
    """
    Agent responsible for searching the RAG knowledge base.

    This agent:
    1. Analyzes the user's task description
    2. Searches the vector database for relevant examples
    3. Returns top-k most relevant code examples with scores
    """

    def __init__(self, llm: BaseChatModel, rag_system=None):
        super().__init__("retriever", llm)
        self.rag_system = rag_system

    def search(self, task: str, k: int = 5) -> List[Tuple[any, float]]:
        """
        Search RAG knowledge base for relevant examples.

        Args:
            task: User's task description
            k: Number of examples to retrieve

        Returns:
            List of (document, score) tuples, sorted by relevance
        """
        if not self.rag_system:
            logger.warning("[Retriever] No RAG system available")
            return []

        logger.info(f"[Retriever] Searching for: '{task[:60]}{'...' if len(task) > 60 else ''}'")

        try:
            # Retrieve documents with similarity scores
            results = self.rag_system.retrieve_with_scores(
                query=task,
                k=k,
                score_threshold=0.0  # Get all results, let approver decide
            )

            if not results:
                logger.info("[Retriever] No examples found in knowledge base")
                return []

            # Log what was found
            logger.info(f"[Retriever] Found {len(results)} examples:")
            for i, (doc, score) in enumerate(results, 1):
                category = doc.metadata.get('category', 'unknown')
                tags = doc.metadata.get('tags', '')
                first_line = doc.page_content.split('\n')[0][:50]
                logger.info(f"[Retriever]   [{i}] {category:12s} (score: {score:.3f}) - {first_line}...")
                if tags:
                    logger.info(f"[Retriever]       Tags: {tags}")

            return results

        except Exception as e:
            logger.error(f"[Retriever] Search failed: {e}")
            return []

    def format_examples_for_approval(self, results: List[Tuple[any, float]]) -> str:
        """
        Format retrieved examples for the approver agent.

        Args:
            results: List of (document, score) tuples

        Returns:
            Formatted string with examples and metadata
        """
        if not results:
            return "No examples found in knowledge base."

        parts = ["Retrieved examples from knowledge base:\n"]

        for i, (doc, score) in enumerate(results, 1):
            category = doc.metadata.get('category', 'unknown')
            tags = doc.metadata.get('tags', '')

            parts.append(f"\n--- Example {i} ---")
            parts.append(f"Category: {category}")
            parts.append(f"Relevance Score: {score:.3f}")
            if tags:
                parts.append(f"Tags: {tags}")
            parts.append(f"\nContent:\n{doc.page_content}")
            parts.append("-" * 50)

        return "\n".join(parts)
