"""
Generator Agent — writes Lua code with RAG support.
On retry: receives previous errors and fixes them (like ChatDev's Programmer + error context).
Uses RAG to retrieve relevant examples and reduce hallucinations.
Supports template-based generation when approved examples are provided.
"""

from agents.base import BaseAgent
from langchain_core.language_models import BaseChatModel
from typing import Optional
import logging

logger = logging.getLogger("localscript.agents")


class GeneratorAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, rag_system=None):
        super().__init__("generator", llm)
        self.rag_system = rag_system
        self.use_rag = rag_system is not None

    def generate(
        self,
        task: str,
        errors: str | None = None,
        review: str | None = None,
        approved_template: str | None = None
    ) -> str:
        """
        Generate or fix Lua code based on task + optional feedback.

        Args:
            task: User's task description
            errors: Previous compilation/runtime errors (if retry)
            review: Reviewer feedback (if retry)
            approved_template: Approved RAG examples to use as template (if available)
        """
        logger.info(f"[Generator] Starting generation (task: {len(task)} chars, errors: {bool(errors)}, review: {bool(review)}, template: {bool(approved_template)})")

        parts = [f"Task: {task}"]

        # Add approved template if provided (takes priority over RAG search)
        if approved_template and not errors and not review:
            parts.append(f"\n{approved_template}")
            parts.append("\nIMPORTANT: Use the above examples as templates. Adapt them to solve the specific task.")
            logger.info("[Generator] Using approved RAG template")
        # Fallback to old RAG behavior if no approved template
        elif self.use_rag and not errors and not review and not approved_template:
            # Only use RAG on first generation (not on retries)
            try:
                logger.info("[Generator] Retrieving RAG context...")
                context = self._get_rag_context(task)
                if context:
                    parts.append(f"\n{context}")
                    logger.info(f"[Generator] Added RAG context ({len(context)} chars)")
            except Exception as e:
                logger.warning(f"[Generator] RAG retrieval failed: {e}")

        if errors:
            parts.append(f"\nPrevious code had errors:\n{errors}\n\nFix these errors.")
            logger.info(f"[Generator] Fixing errors ({len(errors)} chars)")
        if review:
            parts.append(f"\nReviewer feedback:\n{review}\n\nApply these improvements.")
            logger.info(f"[Generator] Applying review feedback ({len(review)} chars)")

        parts.append("\nWrite the Lua code now:")
        prompt = "\n".join(parts)

        # Use reasoning strategy on first generation (no errors/review = fresh task).
        # On retries (errors or review present), use direct invoke to avoid
        # re-running the full strategy on a fix — the fix prompt is already focused.
        if errors or review:
            logger.info("[Generator] Using direct invoke (retry mode)")
            raw = self.invoke(prompt)
        else:
            logger.info("[Generator] Using strategy-based invoke (first attempt)")
            raw = self.invoke_with_strategy(prompt)

        # LLMs often wrap code in ```lua ... ``` despite prompt instructions — strip it
        logger.info(f"[Generator] Stripping code fences from response ({len(raw)} chars)")
        cleaned = self.strip_code_fences(raw)
        logger.info(f"[Generator] Code generation complete ({len(cleaned)} chars)")
        return cleaned

    def _get_rag_context(self, task: str, k: int = 3, max_length: int = 1500) -> str:
        """
        Retrieve relevant examples from RAG system.

        Args:
            task: Task description
            k: Number of examples to retrieve
            max_length: Maximum context length

        Returns:
            Formatted context string
        """
        if not self.rag_system:
            return ""

        # Visual feedback: RAG search starting
        print("\n[RAG] Searching knowledge base...")
        print(f"[RAG] Query: '{task[:60]}{'...' if len(task) > 60 else ''}'")

        # Retrieve relevant documents with scores
        try:
            documents_with_scores = self.rag_system.retrieve_with_scores(task, k=k, score_threshold=0.0)
        except:
            # Fallback to regular retrieve if retrieve_with_scores not available
            documents = self.rag_system.retrieve(task, k=k)
            documents_with_scores = [(doc, 0.0) for doc in documents]

        if not documents_with_scores:
            print("[RAG] No relevant examples found")
            return ""

        # Visual feedback: Show what was found
        print(f"[RAG] Found {len(documents_with_scores)} relevant examples:")
        for i, (doc, score) in enumerate(documents_with_scores, 1):
            category = doc.metadata.get('category', 'unknown')
            # Get first line of content as preview
            first_line = doc.page_content.split('\n')[0][:50]
            score_display = f"{score:.3f}" if score > 0 else "N/A"
            print(f"[RAG]   [{i}] {category:12s} (score: {score_display}) - {first_line}...")

        # Format context
        documents = [doc for doc, _ in documents_with_scores]
        context = self.rag_system.format_context(documents, max_length=max_length)

        print(f"[RAG] Context prepared: {len(context)} chars")
        return context
