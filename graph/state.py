"""
Shared state for the LocalScript multi-agent LangGraph pipeline.
Inspired by ChatDev's carry_data / clear_context pattern — adapted for LangGraph StateGraph.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Core task
    task: str                          # Original user task description

    # Code lifecycle (inspired by ChatDev's iterative coding phases)
    code: Optional[str]                # Latest generated Lua code
    errors: Optional[str]              # luac / lua runtime errors from Validator
    review: Optional[str]              # Reviewer agent feedback

    # Functional testing (NEW - Aleksandr Bordash requirement)
    test_code: Optional[str]           # Generated functional test cases
    test_results: Optional[dict]       # {"total": int, "passed": int, "failed": int, "details": str}

    # Iteration control (like ChatDev's loop_counter node)
    iterations: int                    # Current retry count
    max_iterations: int                # Max retries before giving up

    # Status signal (like ChatDev's <INFO> Finished keyword stop)
    status: str                        # "generating" | "validating" | "reviewing" | "done" | "failed"

    # Session workspace
    session_dir: str                   # Path to workspace/session_TIMESTAMP/

    # Profiling metrics
    profile_metrics: Optional[dict]    # {"time": float, "memory": int}

    # RAG workflow (NEW - for Retriever + Approver agents)
    rag_results: Optional[list]        # Retrieved documents with scores from RetrieverAgent
    rag_formatted: Optional[str]       # Formatted examples for ApproverAgent evaluation
    rag_decision: Optional[dict]       # ApproverAgent decision: {"approved": bool, "reason": str, ...}
    approved_template: Optional[str]   # Approved RAG template for GeneratorAgent (if decision["approved"])

    # Clarification workflow (NEW - for ClarifierAgent)
    clarification_questions: Optional[list]  # [{"question": str, "options": list, "required": bool}]
    user_answers: Optional[dict]             # {"0": "answer1", "1": "answer2"}
    needs_clarification: bool                # True if waiting for user input
    clarification_attempted: bool            # True if clarification was already tried (avoid loops)

    # Checkpoint workflow (NEW - for CheckpointAgent)
    checkpoint_pending: bool                 # True if waiting for user approval
    checkpoint_action: Optional[str]         # "approve" | "reject" | "alternatives" | "save_to_kb"
    user_feedback: Optional[str]             # User's change request feedback
    alternatives: Optional[list]             # List of alternative code implementations
    save_to_knowledge_base: bool             # True if user wants to save approved code to RAG

    # LangGraph messages (for agent memory within a node)
    messages: Annotated[list, add_messages]
