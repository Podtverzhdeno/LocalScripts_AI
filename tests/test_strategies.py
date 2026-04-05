"""
Strategy unit tests — mock LLM, no API calls.
Tests reasoning strategies and their integration with agents.
"""
import pytest
from unittest.mock import MagicMock, patch

from strategies.base import PassthroughStrategy, ReasoningStrategy
from strategies.reflect import ReflectStrategy
from strategies.cot import ChainOfThoughtStrategy
from strategies.registry import get_strategy, list_strategies


def make_llm(*responses: str) -> MagicMock:
    """Create a mock LLM that returns responses in sequence."""
    llm = MagicMock()
    side_effects = [MagicMock(content=r) for r in responses]
    llm.invoke.side_effect = side_effects
    return llm


# --- PassthroughStrategy ---

def test_passthrough_calls_llm_once():
    llm = make_llm("direct answer")
    strategy = PassthroughStrategy(llm)
    result = strategy.run("write fibonacci")
    assert result == "direct answer"
    assert llm.invoke.call_count == 1


# --- ReflectStrategy ---

def test_reflect_calls_llm_three_times():
    llm = make_llm("draft code", "found a bug in line 3", "fixed code")
    strategy = ReflectStrategy(llm)
    result = strategy.run("write fibonacci")
    assert result == "fixed code"
    assert llm.invoke.call_count == 3


def test_reflect_passes_draft_to_critique():
    llm = make_llm("draft code", "critique", "final")
    strategy = ReflectStrategy(llm)
    strategy.run("task")
    # Second call (critique) should contain the draft
    second_call_messages = llm.invoke.call_args_list[1][0][0]
    prompt_text = second_call_messages[-1].content  # HumanMessage
    assert "draft code" in prompt_text


def test_reflect_passes_critique_to_revision():
    llm = make_llm("draft", "bug on line 5", "revised")
    strategy = ReflectStrategy(llm)
    strategy.run("task")
    # Third call (revision) should contain both draft and critique
    third_call_messages = llm.invoke.call_args_list[2][0][0]
    prompt_text = third_call_messages[-1].content
    assert "draft" in prompt_text
    assert "bug on line 5" in prompt_text


# --- ChainOfThoughtStrategy ---

def test_cot_calls_llm_twice():
    llm = make_llm("step 1: use recursion\nstep 2: memoize", "final code")
    strategy = ChainOfThoughtStrategy(llm)
    result = strategy.run("write fibonacci")
    assert result == "final code"
    assert llm.invoke.call_count == 2


def test_cot_passes_reasoning_to_code_generation():
    llm = make_llm("use dynamic programming", "dp code")
    strategy = ChainOfThoughtStrategy(llm)
    strategy.run("write fibonacci")
    # Second call should contain the reasoning
    second_call_messages = llm.invoke.call_args_list[1][0][0]
    prompt_text = second_call_messages[-1].content
    assert "use dynamic programming" in prompt_text


# --- Registry ---

def test_get_strategy_none():
    llm = make_llm()
    strategy = get_strategy("none", llm)
    assert isinstance(strategy, PassthroughStrategy)


def test_get_strategy_reflect():
    llm = make_llm()
    strategy = get_strategy("reflect", llm)
    assert isinstance(strategy, ReflectStrategy)


def test_get_strategy_cot():
    llm = make_llm()
    strategy = get_strategy("cot", llm)
    assert isinstance(strategy, ChainOfThoughtStrategy)


def test_get_strategy_unknown_raises():
    llm = make_llm()
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("nonexistent", llm)


def test_list_strategies_contains_all():
    strategies = list_strategies()
    assert "none" in strategies
    assert "reflect" in strategies
    assert "cot" in strategies
    assert len(strategies) >= 3


# --- Integration with BaseAgent ---

def test_generator_uses_strategy_on_first_call():
    """Generator should use strategy on fresh generation (no errors/review)."""
    from agents.generator import GeneratorAgent

    llm = make_llm("draft", "critique", "final code")
    agent = GeneratorAgent(llm)

    with patch("agents.base.get_strategy_name", return_value="reflect"):
        code = agent.generate(task="write fibonacci")

    # reflect = 3 LLM calls
    assert llm.invoke.call_count == 3
    assert code == "final code"


def test_generator_skips_strategy_on_retry():
    """Generator should NOT use strategy when fixing errors (direct invoke)."""
    from agents.generator import GeneratorAgent

    llm = make_llm("fixed code")
    agent = GeneratorAgent(llm)

    with patch("agents.base.get_strategy_name", return_value="reflect"):
        code = agent.generate(task="write fibonacci", errors="syntax error on line 1")

    # Direct invoke = 1 LLM call (no strategy)
    assert llm.invoke.call_count == 1
    assert code == "fixed code"


def test_generator_skips_strategy_on_review_feedback():
    """Generator should NOT use strategy when applying review feedback."""
    from agents.generator import GeneratorAgent

    llm = make_llm("improved code")
    agent = GeneratorAgent(llm)

    with patch("agents.base.get_strategy_name", return_value="reflect"):
        code = agent.generate(task="write fibonacci", review="add error handling")

    assert llm.invoke.call_count == 1
    assert code == "improved code"


def test_generator_no_strategy_when_none():
    """With strategy='none', generator behaves exactly as before."""
    from agents.generator import GeneratorAgent

    llm = make_llm('print("hello")')
    agent = GeneratorAgent(llm)

    with patch("agents.base.get_strategy_name", return_value="none"):
        code = agent.generate(task="print hello")

    assert llm.invoke.call_count == 1
    assert code == 'print("hello")'
