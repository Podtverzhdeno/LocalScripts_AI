"""
Agent unit tests — mock LLM, no API calls.
"""
import pytest
import tempfile
from unittest.mock import MagicMock, patch
from agents.base import BaseAgent
from agents.generator import GeneratorAgent
from agents.validator import ValidatorAgent
from agents.reviewer import ReviewerAgent
from tools.lua_runner import LuaResult


def make_llm(response: str) -> MagicMock:
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content=response)
    return llm


# --- GeneratorAgent ---

def test_generator_basic_task():
    llm = make_llm('print("hello")')
    agent = GeneratorAgent(llm)
    code = agent.generate(task="print hello")
    assert code == 'print("hello")'
    llm.invoke.assert_called_once()


def test_generator_with_errors():
    llm = make_llm("fixed code")
    agent = GeneratorAgent(llm)
    code = agent.generate(task="sort table", errors="undefined variable x")
    assert code == "fixed code"
    # errors should appear in prompt
    call_args = llm.invoke.call_args[0][0]
    assert any("undefined variable x" in m.content for m in call_args)


def test_generator_with_review():
    llm = make_llm("improved code")
    agent = GeneratorAgent(llm)
    code = agent.generate(task="sort table", review="add error handling")
    assert code == "improved code"
    call_args = llm.invoke.call_args[0][0]
    assert any("add error handling" in m.content for m in call_args)


def test_generator_no_errors_no_review():
    llm = make_llm('local x = 1')
    agent = GeneratorAgent(llm)
    code = agent.generate(task="define x")
    assert code == "local x = 1"


# --- ValidatorAgent ---

def test_validator_valid_code():
    llm = make_llm("No errors found.")
    with tempfile.TemporaryDirectory() as d:
        from tools.lua_runner import LuaRunner
        runner = MagicMock(spec=LuaRunner)
        runner.execute.return_value = LuaResult(success=True, stdout="55", stderr="")
        agent = ValidatorAgent(llm, runner)
        is_valid, explanation = agent.validate(code='print(1)', task="test", iteration=1)
    assert is_valid is True
    assert explanation == ""
    llm.invoke.assert_not_called()  # LLM not called if code is valid


def test_validator_invalid_code_calls_llm():
    llm = make_llm("Line 1: unexpected symbol near '!'")
    with tempfile.TemporaryDirectory() as d:
        from tools.lua_runner import LuaRunner
        runner = MagicMock(spec=LuaRunner)
        runner.execute.return_value = LuaResult(success=False, stdout="", stderr="unexpected symbol near '!'")
        agent = ValidatorAgent(llm, runner)
        is_valid, explanation = agent.validate(code="invalid!!!", task="test", iteration=1)
    assert is_valid is False
    assert "unexpected symbol" in explanation
    llm.invoke.assert_called_once()


# --- ReviewerAgent ---

def test_reviewer_approves_with_stop_signal():
    llm = make_llm("Code looks great. <INFO> Finished")
    agent = ReviewerAgent(llm)
    is_done, feedback = agent.review(code='print("ok")', task="test")
    assert is_done is True
    assert "<INFO> Finished" in feedback


def test_reviewer_requests_improvements():
    llm = make_llm("Missing error handling for nil values.")
    agent = ReviewerAgent(llm)
    is_done, feedback = agent.review(code='print("ok")', task="test")
    assert is_done is False
    assert "nil values" in feedback


def test_reviewer_calls_llm():
    llm = make_llm("<INFO> Finished")
    agent = ReviewerAgent(llm)
    agent.review(code="local x = 1", task="define x")
    llm.invoke.assert_called_once()


# --- strip_code_fences ---

def test_strip_code_fences_lua_block():
    raw = '```lua\nprint("hello")\n```'
    assert BaseAgent.strip_code_fences(raw) == 'print("hello")'


def test_strip_code_fences_generic_block():
    raw = '```\nlocal x = 1\n```'
    assert BaseAgent.strip_code_fences(raw) == 'local x = 1'


def test_strip_code_fences_no_fences():
    raw = 'print("hello")'
    assert BaseAgent.strip_code_fences(raw) == 'print("hello")'


def test_strip_code_fences_multiline():
    raw = '```lua\nlocal x = 1\nprint(x)\n```'
    assert BaseAgent.strip_code_fences(raw) == 'local x = 1\nprint(x)'


def test_strip_code_fences_with_surrounding_text():
    raw = 'Here is the code:\n```lua\nprint(1)\n```\nDone.'
    assert BaseAgent.strip_code_fences(raw) == 'print(1)'


def test_generator_strips_markdown_fences():
    """Generator must return clean Lua even if LLM wraps in markdown."""
    llm = make_llm('```lua\nprint("hello")\n```')
    agent = GeneratorAgent(llm)
    code = agent.generate(task="print hello")
    assert code == 'print("hello")'
