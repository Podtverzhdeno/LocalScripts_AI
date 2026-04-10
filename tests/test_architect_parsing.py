"""
Test Architect JSON parsing with mock responses.
"""

from agents.architect import ArchitectAgent
import json


class MockLLM:
    """Mock LLM that returns predefined responses."""

    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        class MockResponse:
            def __init__(self, content):
                self.content = content
        return MockResponse(self.response)


def test_json_parsing():
    """Test different JSON response formats."""

    # Test 1: Clean JSON
    print("Test 1: Clean JSON")
    mock_llm = MockLLM('''{
  "files": [
    {"name": "main.lua", "purpose": "Main logic", "dependencies": []}
  ],
  "structure": "Simple project",
  "order": ["main.lua"]
}''')

    architect = ArchitectAgent(mock_llm)
    try:
        plan = architect.plan("test")
        print(f"  [OK] Parsed: {len(plan['files'])} files")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")

    # Test 2: JSON in markdown
    print("\nTest 2: JSON in markdown code block")
    mock_llm = MockLLM('''Here's the plan:
```json
{
  "files": [
    {"name": "config.lua", "purpose": "Config", "dependencies": []}
  ],
  "structure": "Config-based",
  "order": ["config.lua"]
}
```''')

    architect = ArchitectAgent(mock_llm)
    try:
        plan = architect.plan("test")
        print(f"  [OK] Parsed: {len(plan['files'])} files")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")

    # Test 3: JSON with trailing comma (invalid but common)
    print("\nTest 3: JSON with trailing comma")
    mock_llm = MockLLM('''{
  "files": [
    {"name": "app.lua", "purpose": "App", "dependencies": []},
  ],
  "structure": "App structure",
  "order": ["app.lua"],
}''')

    architect = ArchitectAgent(mock_llm)
    try:
        plan = architect.plan("test")
        print(f"  [OK] Parsed: {len(plan['files'])} files")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")

    # Test 4: JSON with explanation before
    print("\nTest 4: JSON with explanation")
    mock_llm = MockLLM('''I'll create a simple calculator project.

{
  "files": [
    {"name": "calc.lua", "purpose": "Calculator", "dependencies": []}
  ],
  "structure": "Calculator app",
  "order": ["calc.lua"]
}''')

    architect = ArchitectAgent(mock_llm)
    try:
        plan = architect.plan("test")
        print(f"  [OK] Parsed: {len(plan['files'])} files")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")

    print("\n" + "="*50)
    print("JSON parsing tests complete!")


if __name__ == "__main__":
    test_json_parsing()
