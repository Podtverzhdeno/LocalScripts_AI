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
        return "fail"
    if state["status"] == "generating":
        return "generate"
    return "review"


def review_done_or_retry(state: AgentState) -> str:
    """After review: done, retry, or fail."""
    if state["status"] == "done":
        return END
    if state["iterations"] >= state["max_iterations"]:
        return "fail"
    return "generate"


def build_pipeline(llm: BaseChatModel) -> StateGraph:
    """Build and compile the LangGraph StateGraph with injected LLM."""
    node_generate, node_validate, node_review, node_fail = make_nodes(llm)

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
) -> AgentState:
    """
    Entry point. If llm is None, loads from settings.yaml.
    Accepts external llm for testing without API keys.
    """
    if llm is None:
        from llm.factory import get_llm
        llm = get_llm()

    pipeline = build_pipeline(llm)

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
