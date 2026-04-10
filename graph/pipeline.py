"""
LocalScript LangGraph pipeline.
LLM injected once at build time — nodes use closure, no re-init per call.

Flow:
  START → generate → validate → (errors? → generate) → review → END
                        ↓ max_iterations reached → fail → END
"""

from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from graph.state import AgentState
from graph.nodes import make_nodes, _save_final


def should_retry_or_fail(state: AgentState) -> str:
    """After validate: retry, clarify errors, checkpoint, or fail."""
    if state["iterations"] >= state["max_iterations"]:
        return "fail"
    if state["status"] == "generating":
        # Check if we should clarify errors after repeated failures
        if state["iterations"] >= 2 and not state.get("clarification_attempted", False):
            return "clarify_errors"
        return "generate"
    if state["status"] == "reviewing":
        # Go to checkpoint before review
        return "checkpoint"
    return "review"


def review_done_or_retry(state: AgentState) -> str:
    """After review: done, retry, or fail."""
    if state["status"] == "done":
        return END
    if state["iterations"] >= state["max_iterations"]:
        return "fail"
    return "generate"


def clarify_decision(state: AgentState) -> str:
    """After clarify: wait for user or continue."""
    if state.get("needs_clarification", False):
        return "wait_user"
    # Continue to RAG workflow
    return "rag_retrieve"


def clarify_errors_decision(state: AgentState) -> str:
    """After clarify_errors: wait for user or retry generation."""
    if state.get("needs_clarification", False):
        return "wait_user"
    return "generate"


def checkpoint_decision(state: AgentState) -> str:
    """After checkpoint: wait for user approval or continue to review."""
    if state.get("checkpoint_pending", False):
        return "wait_approval"
    return "review"


def process_checkpoint_decision(state: AgentState) -> str:
    """After processing checkpoint: generate, review, or select alternative."""
    status = state.get("status", "")
    if status == "generating":
        return "generate"
    elif status == "selecting_alternative":
        return "wait_alternative"
    return "review"


def build_pipeline(
    llm: BaseChatModel,
    *,
    llm_generator: BaseChatModel | None = None,
    llm_validator: BaseChatModel | None = None,
    llm_reviewer: BaseChatModel | None = None,
    llm_test_generator: BaseChatModel | None = None,
    llm_retriever: BaseChatModel | None = None,
    llm_approver: BaseChatModel | None = None,
    llm_clarifier: BaseChatModel | None = None,
    llm_checkpoint: BaseChatModel | None = None,
    rag_system=None,
    use_rag_workflow: bool = True,
    use_clarifier: bool = True,
    node_callback=None,
    code_callback=None,
) -> StateGraph:
    """
    Build and compile the LangGraph StateGraph with injected LLM(s).

    Args:
        llm: Default LLM for all agents
        llm_generator: Override LLM for GeneratorAgent
        llm_validator: Override LLM for ValidatorAgent
        llm_reviewer: Override LLM for ReviewerAgent
        llm_test_generator: Override LLM for TestGeneratorAgent
        llm_retriever: Override LLM for RetrieverAgent (RAG search)
        llm_approver: Override LLM for ApproverAgent (RAG approval)
        llm_clarifier: Override LLM for ClarifierAgent (task clarification)
        llm_checkpoint: Override LLM for CheckpointAgent (user approval)
        rag_system: RAG system instance (ChromaDB)
        use_rag_workflow: Enable new RAG workflow (Retriever + Approver agents)
        use_clarifier: Enable ClarifierAgent (disable to avoid event loop issues)
        node_callback: Callback for node events
        code_callback: Callback for code streaming

    Returns:
        Compiled StateGraph
    """
    (node_generate, node_validate, node_review, node_fail,
     node_rag_retrieve, node_rag_approve, node_clarify,
     node_enrich_task, node_checkpoint, node_process_checkpoint,
     node_clarify_errors) = make_nodes(
        llm,
        llm_generator=llm_generator,
        llm_validator=llm_validator,
        llm_reviewer=llm_reviewer,
        llm_test_generator=llm_test_generator,
        llm_retriever=llm_retriever,
        llm_approver=llm_approver,
        llm_clarifier=llm_clarifier,
        llm_checkpoint=llm_checkpoint,
        rag_system=rag_system,
        node_callback=node_callback,
        code_callback=code_callback,
        use_rag_workflow=use_rag_workflow,
    )

    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("generate", node_generate)
    graph.add_node("validate", node_validate)
    graph.add_node("review", node_review)
    graph.add_node("fail", node_fail)

    # Add clarifier nodes only if enabled
    if use_clarifier:
        graph.add_node("clarify", node_clarify)
        graph.add_node("enrich_task", node_enrich_task)
        graph.add_node("clarify_errors", node_clarify_errors)

    graph.add_node("checkpoint", node_checkpoint)
    graph.add_node("process_checkpoint", node_process_checkpoint)

    # Add RAG workflow nodes if enabled
    if use_rag_workflow and rag_system:
        graph.add_node("rag_retrieve", node_rag_retrieve)
        graph.add_node("rag_approve", node_rag_approve)

        if use_clarifier:
            # Full flow: START → clarify → (questions? → wait) → enrich → rag → generate
            graph.add_edge(START, "clarify")
            graph.add_conditional_edges(
                "clarify",
                clarify_decision,
                {"wait_user": "enrich_task", "rag_retrieve": "rag_retrieve"}
            )
            graph.add_edge("enrich_task", "rag_retrieve")
        else:
            # Skip clarifier: START → rag → generate
            graph.add_edge(START, "rag_retrieve")

        graph.add_edge("rag_retrieve", "rag_approve")
        graph.add_edge("rag_approve", "generate")
    else:
        if use_clarifier:
            # Direct workflow with clarifier: START → clarify → generate (no RAG)
            graph.add_edge(START, "clarify")
            graph.add_conditional_edges(
                "clarify",
                clarify_decision,
                {"wait_user": "enrich_task", "rag_retrieve": "generate"}
            )
            graph.add_edge("enrich_task", "generate")
        else:
            # Simplest workflow: START → generate (no RAG, no clarifier)
            graph.add_edge(START, "generate")

    graph.add_edge("generate", "validate")

    # Validate decision: retry, clarify errors, checkpoint, or fail
    if use_clarifier:
        graph.add_conditional_edges(
            "validate",
            should_retry_or_fail,
            {
                "generate": "generate",
                "clarify_errors": "clarify_errors",
                "checkpoint": "checkpoint",
                "fail": "fail"
            },
        )

        # Clarify errors decision: wait for user or retry
        graph.add_conditional_edges(
            "clarify_errors",
            clarify_errors_decision,
            {"wait_user": "enrich_task", "generate": "generate"}
        )
    else:
        # Without clarifier: skip clarify_errors
        graph.add_conditional_edges(
            "validate",
            should_retry_or_fail,
            {
                "generate": "generate",
                "clarify_errors": "generate",  # Skip clarify_errors, go directly to generate
                "checkpoint": "checkpoint",
                "fail": "fail"
            },
        )

    # Checkpoint decision: wait for approval or continue to review
    graph.add_conditional_edges(
        "checkpoint",
        checkpoint_decision,
        {"wait_approval": "process_checkpoint", "review": "review"}
    )

    # Process checkpoint decision: generate, review, or wait for alternative selection
    graph.add_conditional_edges(
        "process_checkpoint",
        process_checkpoint_decision,
        {
            "generate": "generate",
            "review": "review",
            "wait_alternative": "process_checkpoint"  # Loop until user selects
        }
    )

    graph.add_conditional_edges(
        "review",
        review_done_or_retry,
        {END: END, "generate": "generate", "fail": "fail"},
    )
    graph.add_edge("fail", END)

    return graph.compile()


def run_pipeline(
    task: str,
    session_dir: str,
    max_iterations: int = 3,
    llm: BaseChatModel | None = None,
    rag_system=None,
    use_rag_workflow: bool = True,
    use_clarifier: bool = None,
    node_callback=None,
    code_callback=None,
) -> AgentState:
    """
    Entry point. If llm is None, loads from settings.yaml.
    Supports per-agent LLM overrides via config/settings.yaml `agents:` section.
    Accepts external llm for testing without API keys.
    Accepts rag_system for retrieval-augmented generation.
    Accepts use_rag_workflow to enable new Retriever+Approver workflow (default: True).
    Accepts use_clarifier to enable ClarifierAgent (default: from env CLARIFIER_ENABLED).
    Accepts node_callback for real-time progress updates.
    Accepts code_callback for streaming code generation.
    """
    from llm.factory import get_llm
    from config.loader import load_settings
    import os

    # Check if clarifier should be enabled (from env or parameter)
    if use_clarifier is None:
        use_clarifier = os.getenv("CLARIFIER_ENABLED", "true").lower() == "true"

    # Load per-agent LLMs from config (returns default if no override)
    if llm is None:
        llm = get_llm()
        llm_generator = get_llm("generator")
        llm_validator = get_llm("validator")
        llm_reviewer = get_llm("reviewer")
        llm_test_generator = get_llm("test_generator")
        llm_retriever = get_llm("retriever")
        llm_approver = get_llm("approver")
        llm_clarifier = get_llm("clarifier")
        llm_checkpoint = get_llm("checkpoint")
    else:
        # External LLM provided (e.g. tests) — use it for all agents
        llm_generator = llm_validator = llm_reviewer = llm_test_generator = None
        llm_retriever = llm_approver = llm_clarifier = llm_checkpoint = None

    # Initialize RAG if enabled and not provided
    if rag_system is None:
        settings = load_settings()
        rag_config = settings.get("rag", {})
        if rag_config.get("enabled", False):
            try:
                print("\n" + "="*60)
                print("[RAG] Initializing Knowledge Base...")
                print("="*60)
                from rag import create_rag_system, initialize_rag_with_examples
                rag_system = create_rag_system(rag_config)

                stats = rag_system.get_stats()
                if stats['total_documents'] == 0:
                    print("[RAG] Empty database detected, loading examples...")
                    initialize_rag_with_examples(rag_system)
                    stats = rag_system.get_stats()

                print(f"[RAG] Status: ACTIVE")
                print(f"[RAG] Documents: {stats['total_documents']}")
                print(f"[RAG] Model: {stats['embedding_model']}")
                print(f"[RAG] Location: {stats['persist_directory']}")
                print(f"[RAG] Workflow: {'NEW (Retriever+Approver)' if use_rag_workflow else 'LEGACY (direct injection)'}")
                print("="*60 + "\n")
            except Exception as e:
                print(f"[RAG] Failed to initialize: {e}")
                rag_system = None
                use_rag_workflow = False

    pipeline = build_pipeline(
        llm,
        llm_generator=llm_generator,
        llm_validator=llm_validator,
        llm_reviewer=llm_reviewer,
        llm_test_generator=llm_test_generator,
        llm_retriever=llm_retriever,
        llm_approver=llm_approver,
        llm_clarifier=llm_clarifier,
        llm_checkpoint=llm_checkpoint,
        rag_system=rag_system,
        use_rag_workflow=use_rag_workflow,
        use_clarifier=use_clarifier,
        node_callback=node_callback,
        code_callback=code_callback,
    )

    initial_state: AgentState = {
        "task": task,
        "code": None,
        "errors": None,
        "review": None,
        "test_code": None,
        "test_results": None,
        "iterations": 0,
        "max_iterations": max_iterations,
        "status": "generating",
        "session_dir": session_dir,
        "profile_metrics": None,
        "messages": [],
        # RAG workflow fields
        "rag_results": None,
        "rag_formatted": None,
        "rag_decision": None,
        "approved_template": None,
        # Clarification workflow fields
        "clarification_questions": None,
        "user_answers": None,
        "needs_clarification": False,
        "clarification_attempted": False,
        # Checkpoint workflow fields
        "checkpoint_pending": False,
        "checkpoint_action": None,
        "user_feedback": None,
        "alternatives": None,
        "save_to_knowledge_base": False,
    }

    return pipeline.invoke(initial_state)
