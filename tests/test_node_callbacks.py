#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal test to verify node callbacks are working.
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_callbacks():
    """Test that node callbacks are invoked."""
    from graph.pipeline import run_pipeline
    from langchain_ollama import ChatOllama

    print("[TEST] Testing Node Callbacks\n")

    # Track which nodes were called
    called_nodes = []

    def callback(node_name, state):
        """Callback to track node execution."""
        iteration = state.get('iterations', 0)
        status = state.get('status', 'unknown')
        called_nodes.append({
            'node': node_name,
            'iteration': iteration,
            'status': status
        })
        print(f"[OK] Callback: {node_name} (iteration {iteration}, status {status})")

    # Create a simple mock LLM that returns valid Lua
    class MockLLM:
        def invoke(self, messages):
            class Response:
                content = "function hello() return 'Hello, World!' end"
            return Response()

    print("Running pipeline with mock LLM...\n")

    try:
        result = run_pipeline(
            task="write a hello world function",
            session_dir="./workspace/test_callbacks",
            max_iterations=1,
            llm=MockLLM(),
            node_callback=callback
        )

        print(f"\n[RESULT] Pipeline Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Iterations: {result.get('iterations')}")

        print(f"\n[SUMMARY] Nodes Called: {len(called_nodes)}")
        for i, call in enumerate(called_nodes, 1):
            print(f"   {i}. {call['node']} (iter {call['iteration']})")

        if len(called_nodes) >= 3:
            print("\n[SUCCESS] Callbacks are working correctly!")
            print("   Expected nodes: generate, validate, review")
            return True
        else:
            print(f"\n[WARNING] Only {len(called_nodes)} callbacks received")
            print("   Expected at least 3 (generate, validate, review)")
            return False

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_callbacks()
    sys.exit(0 if success else 1)
