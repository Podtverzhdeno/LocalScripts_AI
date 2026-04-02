"""
Pydantic models for API request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=4096, description="Lua task description")


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
