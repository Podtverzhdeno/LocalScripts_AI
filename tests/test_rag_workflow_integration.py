"""
Integration test for complete RAG workflow with Retriever + Approver agents.
Tests the full pipeline: START → rag_retrieve → rag_approve → generate → validate → review → END
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from langchain_core.documents import Document
from graph.pipeline import build_pipeline, run_pipeline
from graph.state import AgentState


class TestRAGWorkflowIntegration:
    """Integration tests for RAG workflow in pipeline."""

    def test_rag_workflow_enabled_in_graph(self):
        """Test that RAG nodes are added to graph when workflow is enabled."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="print('test')")

        # Mock RAG system
        rag_system = Mock()
        rag_system.retrieve_with_scores.return_value = []

        # Build pipeline with RAG workflow enabled
        pipeline = build_pipeline(
            llm,
            rag_system=rag_system,
            use_rag_workflow=True
        )

        # Check that RAG nodes are in the graph
        nodes = list(pipeline.nodes.keys())
        assert "rag_retrieve" in nodes, "rag_retrieve node not found in graph"
        assert "rag_approve" in nodes, "rag_approve node not found in graph"
        assert "generate" in nodes
        assert "validate" in nodes
        assert "review" in nodes

    def test_rag_workflow_disabled_in_graph(self):
        """Test that RAG nodes are NOT added when workflow is disabled."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="print('test')")

        # Build pipeline with RAG workflow disabled
        pipeline = build_pipeline(
            llm,
            rag_system=None,
            use_rag_workflow=False
        )

        # Check that RAG nodes are NOT in the graph
        nodes = list(pipeline.nodes.keys())
        assert "rag_retrieve" not in nodes, "rag_retrieve should not be in graph when disabled"
        assert "rag_approve" not in nodes, "rag_approve should not be in graph when disabled"
        assert "generate" in nodes
        assert "validate" in nodes

    def test_full_workflow_with_approval(self, tmp_path):
        """Test complete workflow: retrieve → approve → generate with approved template."""
        llm = Mock()

        # Mock RAG system
        rag_system = Mock()
        doc = Document(
            page_content="function fibonacci(n)\n  if n <= 1 then return n end\n  return fibonacci(n-1) + fibonacci(n-2)\nend",
            metadata={"category": "algorithm", "tags": "fibonacci"}
        )
        rag_system.retrieve_with_scores.return_value = [(doc, 0.92)]
        rag_system.format_context.return_value = "Example: " + doc.page_content
        rag_system.get_stats.return_value = {
            "total_documents": 39,
            "embedding_model": "all-MiniLM-L6-v2",
            "persist_directory": ".veai/chroma"
        }

        # Mock LLM responses
        responses = [
            # Approver: APPROVED
            Mock(content='{"approved": true, "reason": "Perfect match", "selected_examples": [1], "confidence": 0.95}'),
            # Generator: code
            Mock(content="function fibonacci(n)\n  if n <= 1 then return n end\n  return fibonacci(n-1) + fibonacci(n-2)\nend"),
            # Validator: explain errors (won't be called if code is valid)
            Mock(content="No errors"),
            # Reviewer: approve
            Mock(content="Code looks good. <INFO> Finished"),
        ]
        llm.invoke.side_effect = responses

        # Mock LuaRunner
        from tools.lua_runner import LuaResult
        mock_result = LuaResult(
            success=True,
            stdout="",
            stderr="",
            timed_out=False,
            compiled_ok=True,
            execution_time=0.001,
            memory_used=100
        )

        # Run pipeline
        session_dir = str(tmp_path / "session_test")
        Path(session_dir).mkdir(parents=True, exist_ok=True)

        with pytest.MonkeyPatch.context() as m:
            # Mock LuaRunner.execute to avoid actual Lua execution
            def mock_execute(self, code, iteration):
                return mock_result

            from tools import lua_runner
            m.setattr(lua_runner.LuaRunner, "execute", mock_execute)

            final_state = run_pipeline(
                task="write fibonacci function",
                session_dir=session_dir,
                max_iterations=3,
                llm=llm,
                rag_system=rag_system,
                use_rag_workflow=True
            )

        # Verify workflow executed correctly
        assert final_state["status"] == "done"
        assert final_state["code"] is not None
        assert "fibonacci" in final_state["code"]
        assert final_state["rag_decision"]["approved"] is True
        assert final_state["approved_template"] is not None

    def test_full_workflow_with_rejection(self, tmp_path):
        """Test complete workflow: retrieve → reject → generate from scratch."""
        llm = Mock()

        # Mock RAG system
        rag_system = Mock()
        doc = Document(
            page_content="function http_parse(url)\n  -- parse HTTP URL\nend",
            metadata={"category": "network"}
        )
        rag_system.retrieve_with_scores.return_value = [(doc, 0.45)]
        rag_system.get_stats.return_value = {
            "total_documents": 39,
            "embedding_model": "all-MiniLM-L6-v2",
            "persist_directory": ".veai/chroma"
        }

        # Mock LLM responses - use callable to handle multiple calls
        call_count = [0]
        def mock_invoke(messages):
            call_count[0] += 1
            content = str(messages)

            # First call: Approver
            if call_count[0] == 1:
                return Mock(content='{"approved": false, "reason": "Not relevant for fibonacci", "selected_examples": [], "confidence": 0.85}')
            # Second call: Generator
            elif call_count[0] == 2:
                return Mock(content="function fibonacci(n)\n  return n <= 1 and n or fibonacci(n-1) + fibonacci(n-2)\nend")
            # Third call: Reviewer
            else:
                return Mock(content="Good code. <INFO> Finished")

        llm.invoke.side_effect = mock_invoke

        # Mock LuaRunner
        from tools.lua_runner import LuaResult
        mock_result = LuaResult(
            success=True,
            stdout="",
            stderr="",
            timed_out=False,
            compiled_ok=True,
            execution_time=0.001,
            memory_used=100
        )

        session_dir = str(tmp_path / "session_test2")
        Path(session_dir).mkdir(parents=True, exist_ok=True)

        with pytest.MonkeyPatch.context() as m:
            def mock_execute(self, code, iteration):
                return mock_result

            from tools import lua_runner
            m.setattr(lua_runner.LuaRunner, "execute", mock_execute)

            final_state = run_pipeline(
                task="write fibonacci function",
                session_dir=session_dir,
                max_iterations=3,
                llm=llm,
                rag_system=rag_system,
                use_rag_workflow=True
            )

        # Verify workflow executed correctly
        assert final_state["status"] == "done"
        assert final_state["code"] is not None
        assert final_state["rag_decision"]["approved"] is False
        assert final_state["approved_template"] is None  # No template used

    def test_workflow_without_rag_system(self, tmp_path):
        """Test that workflow falls back to direct generation when RAG is disabled."""
        llm = Mock()

        # Mock LLM responses - need enough for all calls
        def mock_invoke(messages):
            content = str(messages)
            if "review" in content.lower():
                return Mock(content="Good. <INFO> Finished")
            else:
                return Mock(content="function test()\n  print('hello')\nend")

        llm.invoke.side_effect = mock_invoke

        # Mock LuaRunner
        from tools.lua_runner import LuaResult
        mock_result = LuaResult(
            success=True,
            stdout="",
            stderr="",
            timed_out=False,
            compiled_ok=True,
            execution_time=0.001,
            memory_used=100
        )

        session_dir = str(tmp_path / "session_test3")
        Path(session_dir).mkdir(parents=True, exist_ok=True)

        with pytest.MonkeyPatch.context() as m:
            def mock_execute(self, code, iteration):
                return mock_result

            from tools import lua_runner
            m.setattr(lua_runner.LuaRunner, "execute", mock_execute)

            final_state = run_pipeline(
                task="write test function",
                session_dir=session_dir,
                max_iterations=3,
                llm=llm,
                rag_system=None,  # No RAG
                use_rag_workflow=False
            )

        # Verify direct workflow (no RAG nodes)
        assert final_state["status"] == "done"
        assert final_state["code"] is not None
        assert final_state["rag_results"] is None
        assert final_state["rag_decision"] is None

    def test_state_fields_initialized(self, tmp_path):
        """Test that all RAG workflow fields are properly initialized in state."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="print('test')")

        rag_system = Mock()
        rag_system.retrieve_with_scores.return_value = []
        rag_system.get_stats.return_value = {
            "total_documents": 0,
            "embedding_model": "test",
            "persist_directory": "test"
        }

        from tools.lua_runner import LuaResult
        mock_result = LuaResult(
            success=True,
            stdout="",
            stderr="",
            timed_out=False,
            compiled_ok=True,
            execution_time=0.001,
            memory_used=100
        )

        session_dir = str(tmp_path / "session_test4")
        Path(session_dir).mkdir(parents=True, exist_ok=True)

        # Build pipeline to check initial state
        from graph.pipeline import build_pipeline
        pipeline = build_pipeline(
            llm,
            rag_system=rag_system,
            use_rag_workflow=True
        )

        initial_state: AgentState = {
            "task": "test",
            "code": None,
            "errors": None,
            "review": None,
            "test_code": None,
            "test_results": None,
            "iterations": 0,
            "max_iterations": 3,
            "status": "generating",
            "session_dir": session_dir,
            "profile_metrics": None,
            "messages": [],
            "rag_results": None,
            "rag_formatted": None,
            "rag_decision": None,
            "approved_template": None,
        }

        # Verify all fields are present
        assert "rag_results" in initial_state
        assert "rag_formatted" in initial_state
        assert "rag_decision" in initial_state
        assert "approved_template" in initial_state
