"""
Test functional test generation feature.
Verifies that TestGeneratorAgent creates proper test cases.
"""

import pytest
from agents.test_generator import TestGeneratorAgent
from unittest.mock import Mock


def test_test_generator_creates_lua_assertions():
    """Test that TestGeneratorAgent generates Lua assert statements."""
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = """
-- Test 1: valid email
assert(validate_email("user@example.com") == true, "Should accept valid email")

-- Test 2: invalid email
assert(validate_email("invalid") == false, "Should reject invalid email")
"""

    agent = TestGeneratorAgent(mock_llm)

    task = "Write a function to validate email addresses"
    code = "function validate_email(email) return true end"

    test_code = agent.generate_tests(task, code)

    assert "assert(" in test_code
    assert "validate_email" in test_code
    assert "Test 1" in test_code or "Test" in test_code


def test_validator_parse_test_results_all_pass():
    """Test parsing when all tests pass."""
    from agents.validator import ValidatorAgent
    from tools.lua_runner import LuaResult

    mock_llm = Mock()
    mock_runner = Mock()

    agent = ValidatorAgent(mock_llm, mock_runner)

    # Simulate successful execution (no assertion failures)
    result = LuaResult(
        success=True,
        stdout="All tests passed",
        stderr="",
        compiled_ok=True
    )

    test_results = agent._parse_test_results(result)

    assert test_results["failed"] == 0
    assert test_results["passed"] >= 0


def test_validator_parse_test_results_with_failures():
    """Test parsing when some tests fail."""
    from agents.validator import ValidatorAgent
    from tools.lua_runner import LuaResult

    mock_llm = Mock()
    mock_runner = Mock()

    agent = ValidatorAgent(mock_llm, mock_runner)

    # Simulate assertion failure
    result = LuaResult(
        success=False,
        stdout="Test 1 passed",
        stderr="lua: test.lua:10: assertion failed!",
        compiled_ok=True
    )

    test_results = agent._parse_test_results(result)

    assert test_results["failed"] > 0
    assert "assertion failed" in test_results["details"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
