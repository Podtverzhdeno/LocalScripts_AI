#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test to verify small prompts are loaded correctly.
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Test 1: Check auto-detection
print("=" * 60)
print("Test 1: Auto-detection by model name")
print("=" * 60)

test_models = [
    ("qwen2.5-coder:7b", True),
    ("deepseek-r1:8b", True),
    ("llama3.2:3b", True),
    ("qwen2.5-coder:32b", False),
    ("gpt-4o-mini", False),
    ("claude-3-opus", False),
]

for model, should_use_small in test_models:
    os.environ["LLM_MODEL"] = model
    os.environ.pop("USE_SMALL_PROMPTS", None)

    # Clear cache
    from config.loader import load_agent_config
    load_agent_config.cache_clear()

    from config.loader import get_agent_prompt
    prompt = get_agent_prompt("generator")

    # Check if small prompt (should be < 1000 chars)
    is_small = len(prompt) < 1000
    status = "[OK]" if is_small == should_use_small else "[FAIL]"

    print(f"{status} {model:25s} -> {'small' if is_small else 'full':5s} ({len(prompt):4d} chars)")

# Test 2: Explicit override
print("\n" + "=" * 60)
print("Test 2: Explicit USE_SMALL_PROMPTS override")
print("=" * 60)

os.environ["LLM_MODEL"] = "gpt-4o-mini"  # Would normally use full
os.environ["USE_SMALL_PROMPTS"] = "true"

load_agent_config.cache_clear()
prompt = get_agent_prompt("generator")
is_small = len(prompt) < 1000

print(f"{'[OK]' if is_small else '[FAIL]'} gpt-4o-mini + USE_SMALL_PROMPTS=true -> {'small' if is_small else 'full'} ({len(prompt)} chars)")

# Test 3: Compare prompt sizes
print("\n" + "=" * 60)
print("Test 3: Prompt size comparison")
print("=" * 60)

os.environ.pop("USE_SMALL_PROMPTS", None)

roles = ["generator", "validator", "reviewer"]
for role in roles:
    # Full prompt
    os.environ["LLM_MODEL"] = "gpt-4o-mini"
    load_agent_config.cache_clear()
    full_prompt = get_agent_prompt(role)

    # Small prompt
    os.environ["LLM_MODEL"] = "qwen2.5-coder:7b"
    load_agent_config.cache_clear()
    small_prompt = get_agent_prompt(role)

    reduction = (1 - len(small_prompt) / len(full_prompt)) * 100
    print(f"{role:12s}: {len(full_prompt):4d} → {len(small_prompt):4d} chars ({reduction:5.1f}% reduction)")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
