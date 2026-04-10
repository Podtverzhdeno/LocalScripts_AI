"""
Rebuild RAG knowledge base with new LowCode examples from public tasks.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rag import create_rag_system, initialize_rag_with_examples
from config.loader import load_settings

def main():
    print("=" * 60)
    print("RAG Knowledge Base Rebuild")
    print("=" * 60)
    print()

    # Load RAG config
    settings = load_settings()
    rag_config = settings.get("rag", {})

    if not rag_config.get("enabled", False):
        print("RAG is disabled in settings. Enable it first:")
        print("  1. Edit config/settings.yaml")
        print("  2. Set rag.enabled: true")
        return

    print("Creating RAG system...")
    rag_system = create_rag_system(rag_config)

    # Get current stats
    stats = rag_system.get_stats()
    print(f"Current documents: {stats['total_documents']}")
    print()

    # Clear existing data
    if stats['total_documents'] > 0:
        print("Clearing existing knowledge base...")
        # Delete collection and recreate
        try:
            rag_system.vectorstore._client.delete_collection(
                name=rag_system.vectorstore._collection.name
            )
            print("✓ Cleared old data")
        except Exception as e:
            print(f"Warning: Could not clear collection: {e}")

        # Recreate RAG system
        rag_system = create_rag_system(rag_config)

    # Initialize with all examples (including new LowCode ones)
    print("\nInitializing with examples...")
    initialize_rag_with_examples(rag_system)

    # Show new stats
    stats = rag_system.get_stats()
    print()
    print("=" * 60)
    print("RAG Knowledge Base Updated")
    print("=" * 60)
    print(f"Total documents: {stats['total_documents']}")
    print(f"Embedding model: {stats['embedding_model']}")
    print(f"Location: {stats['persist_directory']}")
    print()

    # Test retrieval with LowCode query
    print("Testing retrieval with LowCode query...")
    print("Query: 'последний элемент массива'")
    print()

    docs = rag_system.retrieve("последний элемент массива", k=3)
    for i, doc in enumerate(docs, 1):
        category = doc.metadata.get('category', 'unknown')
        tags = doc.metadata.get('tags', '')
        preview = doc.page_content[:100].replace('\n', ' ')
        print(f"[{i}] {category:12s} | {tags:30s}")
        print(f"    {preview}...")
        print()

    print("=" * 60)
    print("Done! RAG is ready with LowCode examples.")
    print("=" * 60)


if __name__ == "__main__":
    main()
