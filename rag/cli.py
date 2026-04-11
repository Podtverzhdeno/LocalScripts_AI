"""
RAG CLI - Command-line interface for managing the RAG knowledge base.

Usage:
    python -m rag.cli init          # Initialize knowledge base
    python -m rag.cli stats         # Show statistics
    python -m rag.cli search "query" # Search for examples
    python -m rag.cli clear         # Clear all documents
    python -m rag.cli add-example   # Add custom example
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag import create_rag_system, initialize_rag_with_examples
from config.loader import load_settings


def cmd_init(args):
    """Initialize RAG knowledge base."""
    print("Initializing RAG knowledge base...")

    settings = load_settings()
    rag_config = settings.get("rag", {})

    rag = create_rag_system(rag_config)
    initialize_rag_with_examples(rag)

    stats = rag.get_stats()
    print(f"\n[OK] Knowledge base initialized")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Model: {stats['embedding_model']}")
    print(f"  Location: {stats['persist_directory']}")


def cmd_stats(args):
    """Show RAG statistics."""
    settings = load_settings()
    rag_config = settings.get("rag", {})

    rag = create_rag_system(rag_config)
    stats = rag.get_stats()

    print("\nRAG Knowledge Base Statistics:")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Embedding model: {stats['embedding_model']}")
    print(f"  Persist directory: {stats['persist_directory']}")


def cmd_search(args):
    """Search for examples."""
    settings = load_settings()
    rag_config = settings.get("rag", {})

    rag = create_rag_system(rag_config)

    print(f"\nSearching for: {args.query}")
    print("="*60)

    results = rag.retrieve_with_scores(args.query, k=args.k)

    if not results:
        print("No results found.")
        return

    for i, (doc, score) in enumerate(results, 1):
        print(f"\n[{i}] Score: {score:.3f}")
        print(f"Category: {doc.metadata.get('category', 'N/A')}")
        print(f"Tags: {doc.metadata.get('tags', 'N/A')}")
        print("-" * 60)
        print(doc.page_content[:500])
        if len(doc.page_content) > 500:
            print("...")


def cmd_clear(args):
    """Clear all documents."""
    if not args.force:
        response = input("Are you sure you want to clear all documents? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return

    settings = load_settings()
    rag_config = settings.get("rag", {})

    rag = create_rag_system(rag_config)
    rag.clear()

    print("[OK] Knowledge base cleared")


def cmd_add_example(args):
    """Add custom code example."""
    settings = load_settings()
    rag_config = settings.get("rag", {})

    rag = create_rag_system(rag_config)

    print("\nAdd Custom Example")
    print("="*60)

    description = input("Description: ")
    category = input("Category (algorithm/pattern/stdlib/best-practice): ")

    print("Enter Lua code (press Ctrl+D or Ctrl+Z when done):")
    code_lines = []
    try:
        while True:
            line = input()
            code_lines.append(line)
    except EOFError:
        pass

    code = "\n".join(code_lines)

    rag.add_code_example(
        code=code,
        description=description,
        category=category
    )

    print("\n[OK] Example added")
    stats = rag.get_stats()
    print(f"  Total documents: {stats['total_documents']}")


def main():
    parser = argparse.ArgumentParser(
        description="RAG Knowledge Base CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m rag.cli init
  python -m rag.cli stats
  python -m rag.cli search "fibonacci memoization"
  python -m rag.cli search "sort array" -k 5
  python -m rag.cli clear --force
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    subparsers.add_parser("init", help="Initialize knowledge base")

    # stats command
    subparsers.add_parser("stats", help="Show statistics")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for examples")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", type=int, default=3, help="Number of results (default: 3)")

    # clear command
    clear_parser = subparsers.add_parser("clear", help="Clear all documents")
    clear_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # add-example command
    subparsers.add_parser("add-example", help="Add custom code example")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "stats": cmd_stats,
        "search": cmd_search,
        "clear": cmd_clear,
        "add-example": cmd_add_example
    }

    try:
        commands[args.command](args)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
