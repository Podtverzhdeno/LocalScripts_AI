"""
Pipeline tests — no API calls, mock LLM injected directly.
"""
import pytest
import tempfile, os
from unittest.mock import MagicMock
from langgraph.graph import END
from graph.state import AgentState
from graph.pipeline import should_retry_or_fail, review_done_or_retry, run_pipeline


def make_state(**kwargs) -> AgentState:
    defaults = {
        "task": "write fibonacci",
        "code": 'print("ok")',
        "errors": None,
        "review": None,
        "iterations": 1,
        "max_iterations": 3,
        "status": "validating",
        "session_dir": "/tmp/test_session",
        "messages": [],
    }
    defaults.update(kwargs)
    return defaults


# --- Conditional edge tests ---

def test_should_retry_when_errors_and_under_limit():
    state = make_state(status="generating", iterations=1, max_iterations=3)
    assert should_retry_or_fail(state) == "generate"

def test_should_fail_when_max_iterations_reached():
    state = make_state(status="generating", iterations=3, max_iterations=3)
    assert should_retry_or_fail(state) == "fail"

def test_should_go_to_review_when_valid():
    state = make_state(status="reviewing", iterations=1, max_iterations=3)
    assert should_retry_or_fail(state) == "review"

def test_review_done_returns_end():
    state = make_state(status="done", iterations=1, max_iterations=3)
    assert review_done_or_retry(state) == END

def test_review_retry_when_improvements_needed():
    state = make_state(status="generating", iterations=1, max_iterations=3)
    assert review_done_or_retry(state) == "generate"

def test_review_fail_when_max_reached():
    state = make_state(status="generating", iterations=3, max_iterations=3)
    assert review_done_or_retry(state) == "fail"


# --- End-to-end with mock LLM ---

def make_mock_llm(generator_code: str, reviewer_response: str) -> MagicMock:
    """
    Returns mock LLM that:
    - responds with valid Lua when called from generator
    - responds with reviewer_response when called from reviewer
    """
    call_count = [0]

    def mock_invoke(messages):
        call_count[0] += 1
        content = messages[-1].content if messages else ""
        if "Provide your review" in content:
            return MagicMock(content=reviewer_response)
        if "Explain what is wrong" in content:
            return MagicMock(content="Syntax error on line 1")
        return MagicMock(content=generator_code)

    llm = MagicMock()
    llm.invoke.side_effect = mock_invoke
    return llm


def test_pipeline_success_first_try():
    """Valid code + approving reviewer → done in 1 iteration."""
    valid_lua = 'local function fib(n)\n  if n<=1 then return n end\n  return fib(n-1)+fib(n-2)\nend\nprint(fib(10))'
    llm = make_mock_llm(
        generator_code=valid_lua,
        reviewer_response="<INFO> Finished — great code.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = os.path.join(tmpdir, "session")
        os.makedirs(session_dir)

        result = run_pipeline(
            task="write fibonacci",
            session_dir=session_dir,
            max_iterations=3,
            llm=llm,
        )

    assert result["status"] == "done"
    assert result["iterations"] == 1
    assert result["code"] == valid_lua


def test_pipeline_fails_after_max_iterations():
    """Always-broken code → fail after max_iterations."""
    broken_lua = "invalid lua !@#$"
    llm = make_mock_llm(
        generator_code=broken_lua,
        reviewer_response="<INFO> Finished",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = os.path.join(tmpdir, "session")
        os.makedirs(session_dir)

        result = run_pipeline(
            task="write something",
            session_dir=session_dir,
            max_iterations=2,
            llm=llm,
        )

    assert result["status"] == "failed"
    assert result["iterations"] >= 2


def test_workspace_files_created_on_success():
    """final.lua and report.md must exist after successful run."""
    valid_lua = 'print("hello")'
    llm = make_mock_llm(
        generator_code=valid_lua,
        reviewer_response="<INFO> Finished",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        session_dir = os.path.join(tmpdir, "session")
        os.makedirs(session_dir)

        run_pipeline(
            task="print hello",
            session_dir=session_dir,
            max_iterations=3,
            llm=llm,
        )

        files = os.listdir(session_dir)
        assert "final.lua" in files, f"final.lua missing. Files: {files}"
        assert "report.md" in files, f"report.md missing. Files: {files}"
        assert open(os.path.join(session_dir, "final.lua")).read() == valid_lua
