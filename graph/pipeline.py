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
    """After validate: retry, go to review, or fail."""
    if state["iterations"] >= state["max_iterations"]:
        # If we have valid code, go to review for final check
        # Otherwise fail
        if state.get("errors") is None:
            return "review"
        return "fail"
    if state["status"] == "generating":
        return "generate"
    return "review"


def review_done_or_retry(state: AgentState) -> str:
    """After review: done, retry, or fail."""
    if state["status"] == "done":
        return END
    if state["iterations"] >= state["max_iterations"]:
        # Max iterations reached but reviewer wants improvements
        # Save as partial success instead of complete failure
        return END
    return "generate"


def build_pipeline(
    llm: BaseChatModel,
    *,
    llm_generator: BaseChatModel | None = None,
    llm_validator: BaseChatModel | None = None,
    llm_reviewer: BaseChatModel | None = None,
    rag_system=None,
    node_callback=None,
    code_callback=None,
) -> StateGraph:
    """Build and compile the LangGraph StateGraph with injected LLM(s)."""
    node_generate, node_validate, node_review, node_fail = make_nodes(
        llm,
        llm_generator=llm_generator,
        llm_validator=llm_validator,
        llm_reviewer=llm_reviewer,
        rag_system=rag_system,
        node_callback=node_callback,
        code_callback=code_callback,
    )

    graph = StateGraph(AgentState)

    graph.add_node("generate", node_generate)
    graph.add_node("validate", node_validate)
    graph.add_node("review", node_review)
    graph.add_node("fail", node_fail)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "validate")

    graph.add_conditional_edges(
        "validate",
        should_retry_or_fail,
        {"generate": "generate", "review": "review", "fail": "fail"},
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
    node_callback=None,
    code_callback=None,
) -> AgentState:
    """
    Entry point. If llm is None, loads from settings.yaml.
    Supports per-agent LLM overrides via config/settings.yaml `agents:` section.
    Accepts external llm for testing without API keys.
    Accepts rag_system for retrieval-augmented generation.
    Accepts node_callback for real-time progress updates.
    Accepts code_callback for streaming code generation.
    """
    from llm.factory import get_llm
    from config.loader import load_settings

    # Load per-agent LLMs from config (returns default if no override)
    if llm is None:
        llm = get_llm()
        llm_generator = get_llm("generator")
        llm_validator = get_llm("validator")
        llm_reviewer = get_llm("reviewer")
    else:
        # External LLM provided (e.g. tests) — use it for all agents
        llm_generator = llm_validator = llm_reviewer = None

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
                print("="*60 + "\n")
            except Exception as e:
                print(f"[RAG] Failed to initialize: {e}")
                rag_system = None

    pipeline = build_pipeline(
        llm,
        llm_generator=llm_generator,
        llm_validator=llm_validator,
        llm_reviewer=llm_reviewer,
        rag_system=rag_system,
        node_callback=node_callback,
        code_callback=code_callback,
    )

    initial_state: AgentState = {
        "task": task,
        "code": None,
        "errors": None,
        "review": None,
        "iterations": 0,
        "max_iterations": max_iterations,
        "status": "generating",
        "session_dir": session_dir,
        "messages": [],
    }

    return pipeline.invoke(initial_state)
