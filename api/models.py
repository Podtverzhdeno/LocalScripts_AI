"""
Pydantic models for API request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=4096, description="Task description or project requirements")
    mode: str = Field(default="quick", description="Execution mode: 'quick' or 'project'")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max retry iterations per file")
    evolutions: int = Field(default=3, ge=0, le=10, description="Evolution cycles (project mode only)")


class ClarificationAnswersRequest(BaseModel):
    answers: dict[str, str] = Field(..., description="Map of question index to answer")


class CheckpointDecisionRequest(BaseModel):
    action: str = Field(..., description="Action: 'approve', 'reject', 'alternatives', 'save_to_kb'")
    feedback: str | None = Field(None, description="User feedback for 'reject' action")
    selected_alternative: int | None = Field(None, description="Index of selected alternative")


# ── Responses ─────────────────────────────────────────────────────────────────

class RunTaskResponse(BaseModel):
    session_id: str
    status: str  # "running" | "done" | "failed"
    message: str


class SessionStatus(BaseModel):
    session_id: str
    status: str  # "running" | "done" | "failed" | "unknown"
    task: str | None = None
    iteration: int = 0
    errors: str | None = None
    has_final: bool = False


class SessionListItem(BaseModel):
    session_id: str
    task: str | None = None
    has_final: bool = False


class SessionFile(BaseModel):
    name: str
    size: int  # bytes


class ErrorResponse(BaseModel):
    detail: str
