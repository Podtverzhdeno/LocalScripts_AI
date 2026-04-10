"""
Example: Using the new RAG workflow with Retriever and Approver agents.

This example demonstrates how to use the enhanced RAG system with
separate retrieval and approval stages.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.system import create_rag_system
from rag.knowledge_base import initialize_rag_with_examples
from agents.retriever import RetrieverAgent
from agents.approver import ApproverAgent
from agents.generator import GeneratorAgent
from llm.factory import get_llm


def example_rag_workflow():
    """
    Demonstrate the new RAG workflow:
    1. Retriever searches knowledge base
    2. Approver evaluates relevance
    3. Generator uses approved template or generates from scratch
    """

    print("=" * 60)
    print("RAG Workflow Example: Retriever + Approver + Generator")
    print("=" * 60)

    # Initialize RAG system
    print("\n[1] Initializing RAG system...")
    rag_system = create_rag_system()
    initialize_rag_with_examples(rag_system)
    stats = rag_system.get_stats()
    print(f"    Knowledge base: {stats['total_documents']} documents")

    # Initialize LLMs (you can use different models for each agent)
    print("\n[2] Initializing agents...")
    llm = get_llm()  # Default LLM from config

    retriever = RetrieverAgent(llm, rag_system=rag_system)
    approver = ApproverAgent(llm)
    generator = GeneratorAgent(llm, rag_system=rag_system)

    print("    ✓ Retriever Agent")
    print("    ✓ Approver Agent")
    print("    ✓ Generator Agent")

    # Test task
    task = "write a fibonacci function with memoization"
    print(f"\n[3] Task: {task}")

    # Step 1: Retrieval
    print("\n[4] Retriever searching knowledge base...")
    results = retriever.search(task=task, k=5)

    if not results:
        print("    No examples found!")
        return

    print(f"    Found {len(results)} examples")

    # Step 2: Format for approval
    print("\n[5] Formatting examples for approver...")
    formatted = retriever.format_examples_for_approval(results)
    print(f"    Formatted {len(formatted)} characters")

    # Step 3: Approval
    print("\n[6] Approver evaluating relevance...")
    decision = approver.evaluate(
        task=task,
        retrieved_examples=formatted,
    )

    print(f"\n    Decision: {'✓ APPROVED' if decision['approved'] else '✗ REJECTED'}")
    print(f"    Reason: {decision['reason']}")
    print(f"    Confidence: {decision['confidence']:.2f}")

    if decision['approved']:
        print(f"    Selected examples: {decision['selected_examples']}")

    # Step 4: Generate code
    print("\n[7] Generator writing code...")

    if decision['approved'] and decision['selected_examples']:
        # Extract approved examples
        approved_docs = approver.extract_approved_examples(
            results,
            decision['selected_examples']
        )

        # Format as template
        approved_template = rag_system.format_context(
            [doc for doc, _ in approved_docs],
            max_length=2000
        )

        print("    Using approved template")
        code = generator.generate(
            task=task,
            approved_template=approved_template
        )
    else:
        print("    Generating from scratch")
        code = generator.generate(task=task)

    # Display result
    print("\n[8] Generated code:")
    print("-" * 60)
    print(code)
    print("-" * 60)

    print(f"\n✓ Complete! Generated {len(code)} characters")


def example_comparison():
    """
    Compare old vs new RAG workflow.
    """
    print("=" * 60)
    print("Comparison: Direct RAG vs Retriever+Approver")
    print("=" * 60)

    # Initialize
    rag_system = create_rag_system()
    initialize_rag_with_examples(rag_system)
    llm = get_llm()

    task = "write a stack data structure"

    # Old way: Direct RAG injection
    print("\n[OLD] Direct RAG (no approval):")
    print("-" * 60)
    generator_old = GeneratorAgent(llm, rag_system=rag_system)
    code_old = generator_old.generate(task=task)
    print(f"Generated {len(code_old)} chars")

    # New way: Retriever + Approver
    print("\n[NEW] Retriever + Approver workflow:")
    print("-" * 60)

    retriever = RetrieverAgent(llm, rag_system=rag_system)
    approver = ApproverAgent(llm)
    generator_new = GeneratorAgent(llm, rag_system=rag_system)

    # Retrieve
    results = retriever.search(task=task, k=5)
    formatted = retriever.format_examples_for_approval(results)

    # Approve
    decision = approver.evaluate(task=task, retrieved_examples=formatted)
    print(f"Decision: {'APPROVED' if decision['approved'] else 'REJECTED'}")
    print(f"Reason: {decision['reason']}")

    # Generate
    if decision['approved'] and decision['selected_examples']:
        approved_docs = approver.extract_approved_examples(results, decision['selected_examples'])
        template = rag_system.format_context([doc for doc, _ in approved_docs])
        code_new = generator_new.generate(task=task, approved_template=template)
    else:
        code_new = generator_new.generate(task=task)

    print(f"Generated {len(code_new)} chars")

    print("\n" + "=" * 60)
    print("Key Difference:")
    print("  OLD: All retrieved examples injected directly")
    print("  NEW: Only approved examples used as templates")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG Workflow Examples")
    parser.add_argument(
        "--mode",
        choices=["workflow", "comparison"],
        default="workflow",
        help="Which example to run"
    )

    args = parser.parse_args()

    if args.mode == "workflow":
        example_rag_workflow()
    elif args.mode == "comparison":
        example_comparison()
