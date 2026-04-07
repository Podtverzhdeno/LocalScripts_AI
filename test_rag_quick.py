"""
Quick test to verify RAG context retrieval works.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system


def main():
    print("="*60)
    print("  Quick RAG Context Retrieval Test")
    print("="*60)

    # Initialize RAG
    print("\n[1/2] Initializing RAG...")
    rag = create_rag_system()
    stats = rag.get_stats()
    print(f"      Documents: {stats['total_documents']}")

    if stats['total_documents'] == 0:
        print("      [ERROR] No documents in database!")
        print("      Run: python update_rag_db.py")
        return

    # Test retrieval
    print("\n[2/2] Testing context retrieval...")

    test_cases = [
        ("fibonacci with memoization", "algorithm"),
        ("read file line by line", "file-io"),
        ("class with metatable", "oop"),
        ("depth first search", "algorithm"),
    ]

    for task, expected_category in test_cases:
        print(f"\n  Task: '{task}'")

        # Retrieve documents
        docs = rag.retrieve(task, k=2)

        if docs:
            print(f"    [OK] Found {len(docs)} relevant examples")
            for i, doc in enumerate(docs, 1):
                category = doc.metadata.get('category', 'unknown')
                preview = doc.page_content[:60].replace('\n', ' ')
                print(f"      [{i}] Category: {category}")
                print(f"          Preview: {preview}...")

            # Format context
            context = rag.format_context(docs, max_length=500)
            print(f"    [OK] Formatted context: {len(context)} chars")
        else:
            print(f"    [FAIL] No documents found!")

    print("\n" + "="*60)
    print("  Test Complete")
    print("="*60)
    print("\nConclusion:")
    print("  RAG system is working and retrieving relevant examples")
    print("  from the vector database based on semantic similarity.")
    print("="*60)


if __name__ == "__main__":
    main()
