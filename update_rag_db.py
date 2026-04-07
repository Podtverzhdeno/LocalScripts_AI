"""
Update RAG vector database with new examples.
This script clears the existing database and reinitializes it with all examples.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system, initialize_rag_with_examples


def main():
    print("="*60)
    print("  Updating RAG Vector Database")
    print("="*60)

    # Create RAG system (production database)
    print("\n[1/3] Connecting to vector database...")
    rag = create_rag_system({
        "persist_directory": ".veai/chroma",
        "embedding_model": "all-MiniLM-L6-v2",
        "collection_name": "lua_knowledge"
    })

    # Get current stats
    stats = rag.get_stats()
    print(f"      Current documents: {stats['total_documents']}")

    # Clear existing data
    if stats['total_documents'] > 0:
        print("\n[2/3] Clearing existing documents...")
        rag.clear()
        print("      Database cleared")
    else:
        print("\n[2/3] Database is empty, skipping clear")

    # Reinitialize with all examples
    print("\n[3/3] Adding new examples...")
    initialize_rag_with_examples(rag)

    # Show final stats
    final_stats = rag.get_stats()
    print(f"\n{'='*60}")
    print(f"  SUCCESS - Database Updated")
    print(f"{'='*60}")
    print(f"  Total documents: {final_stats['total_documents']}")
    print(f"  Embedding model: {final_stats['embedding_model']}")
    print(f"  Location: {final_stats['persist_directory']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
