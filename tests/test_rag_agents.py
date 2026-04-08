"""
Tests for Retriever and Approver agents.
"""

import pytest
from unittest.mock import Mock, MagicMock
from agents.retriever import RetrieverAgent
from agents.approver import ApproverAgent
from langchain_core.documents import Document


class TestRetrieverAgent:
    """Tests for RetrieverAgent."""

    def test_search_with_results(self):
        """Test retriever returns results when examples are found."""
        # Mock LLM and RAG system
        llm = Mock()
        rag_system = Mock()

        # Mock search results
        doc1 = Document(
            page_content="Fibonacci with memoization\n```lua\nlocal memo = {}\n```",
            metadata={"category": "algorithm", "tags": "fibonacci,memoization"}
        )
        doc2 = Document(
            page_content="Binary search\n```lua\nlocal function search()\n```",
            metadata={"category": "algorithm", "tags": "search,binary"}
        )

        rag_system.retrieve_with_scores.return_value = [
            (doc1, 0.892),
            (doc2, 0.745),
        ]

        # Create agent and search
        retriever = RetrieverAgent(llm, rag_system=rag_system)
        results = retriever.search(task="write fibonacci", k=5)

        # Verify
        assert len(results) == 2
        assert results[0][0].metadata["category"] == "algorithm"
        assert results[0][1] == 0.892
        rag_system.retrieve_with_scores.assert_called_once()

    def test_search_no_results(self):
        """Test retriever handles empty results."""
        llm = Mock()
        rag_system = Mock()
        rag_system.retrieve_with_scores.return_value = []

        retriever = RetrieverAgent(llm, rag_system=rag_system)
        results = retriever.search(task="write something", k=5)

        assert results == []

    def test_search_no_rag_system(self):
        """Test retriever handles missing RAG system."""
        llm = Mock()
        retriever = RetrieverAgent(llm, rag_system=None)
        results = retriever.search(task="write something", k=5)

        assert results == []

    def test_format_examples_for_approval(self):
        """Test formatting examples for approver."""
        llm = Mock()
        rag_system = Mock()

        doc = Document(
            page_content="Example code",
            metadata={"category": "algorithm", "tags": "test"}
        )

        retriever = RetrieverAgent(llm, rag_system=rag_system)
        formatted = retriever.format_examples_for_approval([(doc, 0.85)])

        assert "Example 1" in formatted
        assert "Category: algorithm" in formatted
        assert "Relevance Score: 0.850" in formatted
        assert "Example code" in formatted

    def test_format_empty_examples(self):
        """Test formatting empty examples list."""
        llm = Mock()
        retriever = RetrieverAgent(llm, rag_system=None)
        formatted = retriever.format_examples_for_approval([])

        assert "No examples found" in formatted


class TestApproverAgent:
    """Tests for ApproverAgent."""

    def test_evaluate_approved(self):
        """Test approver approves relevant examples."""
        llm = Mock()

        # Mock LLM response (approved)
        llm.invoke.return_value = Mock(
            content='{"approved": true, "reason": "Highly relevant", "selected_examples": [1], "confidence": 0.9}'
        )

        approver = ApproverAgent(llm)
        decision = approver.evaluate(
            task="write fibonacci",
            retrieved_examples="Example 1: Fibonacci with memoization"
        )

        assert decision["approved"] is True
        assert decision["reason"] == "Highly relevant"
        assert decision["selected_examples"] == [1]
        assert decision["confidence"] == 0.9

    def test_evaluate_rejected(self):
        """Test approver rejects irrelevant examples."""
        llm = Mock()

        # Mock LLM response (rejected)
        llm.invoke.return_value = Mock(
            content='{"approved": false, "reason": "Not relevant", "selected_examples": [], "confidence": 0.7}'
        )

        approver = ApproverAgent(llm)
        decision = approver.evaluate(
            task="write fibonacci",
            retrieved_examples="Example 1: HTTP parser"
        )

        assert decision["approved"] is False
        assert decision["reason"] == "Not relevant"
        assert decision["selected_examples"] == []
        assert decision["confidence"] == 0.7

    def test_evaluate_no_examples(self):
        """Test approver handles no examples."""
        llm = Mock()
        approver = ApproverAgent(llm)

        decision = approver.evaluate(
            task="write something",
            retrieved_examples=""
        )

        assert decision["approved"] is False
        assert "No examples found" in decision["reason"]
        assert decision["confidence"] == 1.0

    def test_evaluate_json_parse_error(self):
        """Test approver handles invalid JSON response."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="This is not JSON")

        approver = ApproverAgent(llm)
        decision = approver.evaluate(
            task="write something",
            retrieved_examples="Example 1: Test"
        )

        # Should fallback to rejection
        assert decision["approved"] is False
        assert "JSON parse error" in decision["reason"]
        assert decision["confidence"] == 0.0

    def test_extract_approved_examples(self):
        """Test extracting approved examples by indices."""
        llm = Mock()
        approver = ApproverAgent(llm)

        doc1 = Document(page_content="Example 1")
        doc2 = Document(page_content="Example 2")
        doc3 = Document(page_content="Example 3")

        results = [(doc1, 0.9), (doc2, 0.8), (doc3, 0.7)]

        # Extract examples 1 and 3 (1-based indices)
        approved = approver.extract_approved_examples(results, [1, 3])

        assert len(approved) == 2
        assert approved[0][0].page_content == "Example 1"
        assert approved[1][0].page_content == "Example 3"

    def test_extract_invalid_indices(self):
        """Test extracting with invalid indices."""
        llm = Mock()
        approver = ApproverAgent(llm)

        doc1 = Document(page_content="Example 1")
        results = [(doc1, 0.9)]

        # Try to extract index 5 (out of bounds)
        approved = approver.extract_approved_examples(results, [5])

        assert len(approved) == 0


class TestIntegration:
    """Integration tests for Retriever + Approver workflow."""

    def test_full_workflow_approved(self):
        """Test complete workflow with approval."""
        # Mock components
        llm = Mock()
        rag_system = Mock()

        # Mock retrieval
        doc = Document(
            page_content="Fibonacci with memoization",
            metadata={"category": "algorithm"}
        )
        rag_system.retrieve_with_scores.return_value = [(doc, 0.9)]

        # Mock approval
        llm.invoke.return_value = Mock(
            content='{"approved": true, "reason": "Perfect match", "selected_examples": [1], "confidence": 0.95}'
        )

        # Mock format_context
        rag_system.format_context.return_value = "Formatted template"

        # Execute workflow
        retriever = RetrieverAgent(llm, rag_system=rag_system)
        approver = ApproverAgent(llm)

        # Step 1: Retrieve
        results = retriever.search(task="write fibonacci", k=5)
        assert len(results) == 1

        # Step 2: Format
        formatted = retriever.format_examples_for_approval(results)
        assert "Fibonacci" in formatted

        # Step 3: Approve
        decision = approver.evaluate(task="write fibonacci", retrieved_examples=formatted)
        assert decision["approved"] is True

        # Step 4: Extract
        approved_docs = approver.extract_approved_examples(results, decision["selected_examples"])
        assert len(approved_docs) == 1

        # Step 5: Format template
        template = rag_system.format_context([doc for doc, _ in approved_docs])
        assert template == "Formatted template"

    def test_full_workflow_rejected(self):
        """Test complete workflow with rejection."""
        llm = Mock()
        rag_system = Mock()

        # Mock retrieval
        doc = Document(page_content="HTTP parser", metadata={"category": "network"})
        rag_system.retrieve_with_scores.return_value = [(doc, 0.5)]

        # Mock rejection
        llm.invoke.return_value = Mock(
            content='{"approved": false, "reason": "Not relevant", "selected_examples": [], "confidence": 0.8}'
        )

        # Execute workflow
        retriever = RetrieverAgent(llm, rag_system=rag_system)
        approver = ApproverAgent(llm)

        results = retriever.search(task="write fibonacci", k=5)
        formatted = retriever.format_examples_for_approval(results)
        decision = approver.evaluate(task="write fibonacci", retrieved_examples=formatted)

        assert decision["approved"] is False
        assert decision["selected_examples"] == []
        # Should generate from scratch (no template)
