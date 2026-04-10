"""
Simple test of project pipeline logic without LLM calls.
"""

from pathlib import Path
import json

# Mock plan (what Architect would return)
mock_plan = {
    "files": [
        {"name": "config.lua", "purpose": "Configuration", "dependencies": []},
        {"name": "calculator.lua", "purpose": "Calculator logic", "dependencies": ["config.lua"]}
    ],
    "structure": "Simple calculator with config",
    "order": ["config.lua", "calculator.lua"]
}

# Create test project directory
test_dir = Path("workspace/test_project_mock")
test_dir.mkdir(parents=True, exist_ok=True)
src_dir = test_dir / "src"
src_dir.mkdir(exist_ok=True)

# Save mock plan
(test_dir / "project_plan.json").write_text(json.dumps(mock_plan, indent=2), encoding="utf-8")

# Create mock files
(src_dir / "config.lua").write_text("-- Config\nlocal config = {}\nreturn config", encoding="utf-8")
(src_dir / "calculator.lua").write_text("-- Calculator\nfunction add(a, b) return a + b end\nprint(add(2, 3))", encoding="utf-8")

print(f"Mock project created at: {test_dir}")
print(f"Files: {list(src_dir.glob('*.lua'))}")
print("\nProject structure works! Now need to debug Architect JSON parsing.")
