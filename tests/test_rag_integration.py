"""
Test RAG integration in the actual pipeline.
This script runs a real code generation task and shows if RAG context is used.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system, initialize_rag_with_examples
from agents.generator import GeneratorAgent
from llm.factory import get_llm


def test_rag_in_generator():
    """Test that RAG context is actually retrieved and used."""
    print("="*60)
    print("  Testing RAG Integration in Generator")
    print("="*60)

    # Initialize RAG
    print("\n[1/4] Initializing RAG system...")
    rag = create_rag_system()
    stats = rag.get_stats()

    if stats['total_documents'] == 0:
        print("      Initializing knowledge base...")
        initialize_rag_with_examples(rag)
        stats = rag.get_stats()

    print(f"      Documents: {stats['total_documents']}")

    # Create generator with RAG
    print("\n[2/4] Creating generator with RAG...")
    llm = get_llm("generator")
    generator = GeneratorAgent(llm, rag_system=rag)
    print(f"      RAG enabled: {generator.use_rag}")

    # Test different tasks
    test_tasks = [
        "write a fibonacci function with memoization",
        "implement a binary search in a sorted array",
        "create a simple file reader that reads line by line",
        "implement a class using metatables with inheritance"
    ]

    print("\n[3/4] Testing RAG context retrieval...")
    for i, task in enumerate(test_tasks, 1):
        print(f"\n  Task {i}: {task}")

        # Get RAG context (what the generator would retrieve)
        context = generator._get_rag_context(task, k=2)

        if context:
            print(f"    [OK] Retrieved context: {len(context)} chars")
            # Show first 150 chars of context
            preview = context.replace('\n', ' ')[:150]
            print(f"    Preview: {preview}...")
        else:
            print(f"    [FAIL] No context retrieved")

    print("\n[4/4] Testing actual code generation with RAG...")
    task = "write a fibonacci function with memoization"
    print(f"\n  Task: {task}")
    print("  Generating code (this may take a moment)...")

    try:
        code = generator.generate(task)
        print(f"\n  [OK] Code generated: {len(code)} chars")
        print("\n  Generated code preview:")
        print("  " + "-"*56)
        lines = code.split('\n')[:10]
        for line in lines:
            print(f"  {line}")
        if len(code.split('\n')) > 10:
            print("  ...")
        print("  " + "-"*56)
    except Exception as e:
        print(f"\n  [FAIL] Generation failed: {e}")

    print("\n" + "="*60)
    print("  Test Complete")
    print("="*60)


if __name__ == "__main__":
    test_rag_in_generator()
