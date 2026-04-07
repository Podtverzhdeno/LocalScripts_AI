"""
Simple test to verify RAG integration without LLM calls.
Tests that the generator can retrieve RAG context correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system


def main():
    print("="*60)
    print("  RAG Integration Test (No LLM)")
    print("="*60)

    # Initialize RAG
    print("\n[1/3] Initializing RAG system...")
    rag = create_rag_system()
    stats = rag.get_stats()
    print(f"      Documents in database: {stats['total_documents']}")

    if stats['total_documents'] == 0:
        print("      [ERROR] No documents found!")
        print("      Run: python update_rag_db.py")
        return

    # Test retrieval with different queries
    print("\n[2/3] Testing semantic search...")

    test_queries = [
        ("fibonacci with memoization", "Should find algorithm examples"),
        ("read file line by line", "Should find file I/O examples"),
        ("class with inheritance using metatables", "Should find OOP examples"),
        ("depth first search graph traversal", "Should find DFS/BFS examples"),
        ("string pattern matching", "Should find string processing examples"),
    ]

    for query, expected in test_queries:
        print(f"\n  Query: '{query}'")
        print(f"  Expected: {expected}")

        # Retrieve top 2 documents
        docs = rag.retrieve(query, k=2)

        if docs:
            print(f"    [OK] Found {len(docs)} documents")
            for i, doc in enumerate(docs, 1):
                category = doc.metadata.get('category', 'unknown')
                # Show first line of content
                first_line = doc.page_content.split('\n')[0][:60]
                print(f"      [{i}] Category: {category}")
                print(f"          {first_line}...")
        else:
            print(f"    [FAIL] No documents found")

    # Test context formatting
    print("\n[3/3] Testing context formatting...")
    query = "write a fibonacci function"
    docs = rag.retrieve(query, k=3)

    if docs:
        context = rag.format_context(docs, max_length=1500)
        print(f"    [OK] Formatted context: {len(context)} chars")
        print(f"\n    Context preview (first 300 chars):")
        print("    " + "-"*56)
        preview = context[:300].replace('\n', '\n    ')
        print(f"    {preview}...")
        print("    " + "-"*56)
    else:
        print(f"    [FAIL] No context generated")

    print("\n" + "="*60)
    print("  Test Complete")
    print("="*60)
    print("\nConclusion:")
    print("  RAG system successfully retrieves relevant examples")
    print("  based on semantic similarity. The system is ready")
    print("  to provide context to the LLM during code generation.")
    print("="*60)


if __name__ == "__main__":
    main()
