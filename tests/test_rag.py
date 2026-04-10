"""
Test RAG system functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system, initialize_rag_with_examples


def test_rag_initialization():
    """Test RAG system initialization."""
    print("="*60)
    print("Test 1: RAG Initialization")
    print("="*60)

    rag = create_rag_system({
        "persist_directory": ".veai/chroma_test",
        "embedding_model": "all-MiniLM-L6-v2",
        "collection_name": "test_knowledge"
    })

    print("[OK] RAG system created")

    # Initialize with examples
    initialize_rag_with_examples(rag)

    stats = rag.get_stats()
    print(f"[OK] Knowledge base initialized")
    print(f"     Documents: {stats['total_documents']}")
    print(f"     Model: {stats['embedding_model']}")

    assert stats['total_documents'] > 0, "No documents loaded"
    print("\n[SUCCESS] Test 1 passed\n")

    return rag


def test_rag_retrieval(rag):
    """Test RAG retrieval."""
    print("="*60)
    print("Test 2: RAG Retrieval")
    print("="*60)

    queries = [
        "fibonacci with memoization",
        "sort an array",
        "error handling with pcall",
        "module pattern"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = rag.retrieve(query, k=2)

        print(f"  Found {len(results)} results")
        for i, doc in enumerate(results, 1):
            category = doc.metadata.get('category', 'N/A')
            print(f"    [{i}] Category: {category}")
            print(f"        Preview: {doc.page_content[:80]}...")

        assert len(results) > 0, f"No results for query: {query}"

    print("\n[SUCCESS] Test 2 passed\n")


def test_rag_context_formatting(rag):
    """Test context formatting."""
    print("="*60)
    print("Test 3: Context Formatting")
    print("="*60)

    query = "fibonacci memoization"
    documents = rag.retrieve(query, k=3)

    context = rag.format_context(documents, max_length=1000)

    print(f"Query: {query}")
    print(f"Context length: {len(context)} chars")
    print(f"Preview:\n{context[:300]}...")

    assert len(context) > 0, "Empty context"
    assert "Relevant examples" in context, "Missing header"
    assert len(context) <= 1000, "Context too long"

    print("\n[SUCCESS] Test 3 passed\n")


def test_rag_with_generator():
    """Test RAG integration with Generator."""
    print("="*60)
    print("Test 4: RAG + Generator Integration")
    print("="*60)

    from agents.generator import GeneratorAgent
    from llm.factory import get_llm

    # Create RAG
    rag = create_rag_system({
        "persist_directory": ".veai/chroma_test",
        "embedding_model": "all-MiniLM-L6-v2"
    })
    initialize_rag_with_examples(rag)

    # Create generator with RAG
    llm = get_llm("generator")
    generator = GeneratorAgent(llm, rag_system=rag)

    print("[OK] Generator created with RAG")
    print(f"     RAG enabled: {generator.use_rag}")

    # Test context retrieval
    task = "write fibonacci with memoization"
    context = generator._get_rag_context(task, k=2)

    print(f"[OK] Retrieved context for task")
    print(f"     Context length: {len(context)} chars")
    print(f"     Preview: {context[:100]}...")

    assert len(context) > 0, "No context retrieved"

    print("\n[SUCCESS] Test 4 passed\n")


def main():
    print("\n" + "="*60)
    print("  RAG System Tests")
    print("="*60 + "\n")

    try:
        # Test 1: Initialization
        rag = test_rag_initialization()

        # Test 2: Retrieval
        test_rag_retrieval(rag)

        # Test 3: Context formatting
        test_rag_context_formatting(rag)

        # Test 4: Generator integration
        test_rag_with_generator()

        print("="*60)
        print("  ALL TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
