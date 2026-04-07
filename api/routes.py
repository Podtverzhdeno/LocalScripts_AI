"""
FastAPI route definitions.
All endpoints wrap the existing pipeline — no core logic is duplicated.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from api.models import (
    ErrorResponse,
    RunTaskRequest,
    RunTaskResponse,
    SessionFile,
    SessionListItem,
    SessionStatus,
)

logger = logging.getLogger("localscript.api")

router = APIRouter()

# ── In-memory session registry ────────────────────────────────────────────────
# Maps session_id → {"status", "task", "iteration", "errors", "ws_clients"}
_sessions: dict[str, dict[str, Any]] = {}


def _get_workspace_dir() -> Path:
    """Resolve workspace base directory from settings."""
    from config.loader import load_settings
    settings = load_settings()
    return Path(settings["workspace"]["base_dir"])


def _make_session_dir(base_dir: Path) -> tuple[str, Path]:
    """Create a timestamped session directory and return (session_id, path)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"session_{timestamp}"
    session_path = base_dir / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    return session_id, session_path


def _detect_iteration(session_path: Path) -> int:
    """Count iteration_*.lua files to determine current iteration."""
    return len(list(session_path.glob("iteration_*.lua")))


def _session_path(session_id: str) -> Path:
    """Resolve full path for a session, raise 404 if missing."""
    path = _get_workspace_dir() / session_id
    if not path.is_dir():
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return path


# ── WebSocket client management ───────────────────────────────────────────────

async def _broadcast(session_id: str, event: dict) -> None:
    """Send a JSON event to all WebSocket clients watching this session."""
    clients: list[WebSocket] = _sessions.get(session_id, {}).get("ws_clients", [])
    dead: list[WebSocket] = []
    payload = json.dumps(event)
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.remove(ws)


def _make_streaming_callback(session_id: str, loop):
    """Create a callback that streams LLM tokens via WebSocket."""
    def on_llm_new_token(token: str, **kwargs):
        """Called by LangChain when a new token is generated."""
        asyncio.run_coroutine_threadsafe(
            _broadcast(session_id, {
                "event": "token",
                "token": token,
                "agent": kwargs.get("agent", "unknown"),
            }),
            loop
        )
    return on_llm_new_token


# ── Pipeline runner (async wrapper) ──────────────────────────────────────────

async def _run_pipeline_async(
    task: str,
    session_id: str,
    session_dir: str,
    max_iterations: int,
) -> None:
    """Run the LangGraph pipeline in a thread and broadcast progress."""
    from graph.pipeline import run_pipeline

    _sessions[session_id]["status"] = "running"
    await _broadcast(session_id, {"event": "started", "session_id": session_id})

    loop = asyncio.get_running_loop()

    # Node callback for real-time graph updates
    def node_callback(node_name: str, state):
        """Called when a node starts executing."""
        iteration = state.get("iterations", 0)
        asyncio.run_coroutine_threadsafe(
            _broadcast(session_id, {
                "event": "node_enter",
                "node": node_name,
                "agent": node_name,  # generator, validate, review
                "iteration": iteration,
                "status": state.get("status", "unknown"),
            }),
            loop
        )

    # Code streaming callback - simulates token streaming by sending code in chunks
    def code_callback(code: str, agent: str):
        """Called after code generation to simulate streaming."""
        chunk_size = 10  # characters per chunk
        for i in range(0, len(code), chunk_size):
            chunk = code[i:i+chunk_size]
            asyncio.run_coroutine_threadsafe(
                _broadcast(session_id, {
                    "event": "token",
                    "token": chunk,
                    "agent": agent,
                }),
                loop
            )
            # Small delay to simulate streaming
            import time
            time.sleep(0.01)

    try:
        final_state = await loop.run_in_executor(
            None,
            lambda: run_pipeline(
                task=task,
                session_dir=session_dir,
                max_iterations=max_iterations,
                node_callback=node_callback,
                code_callback=code_callback,
            ),
        )
        status = final_state.get("status", "failed")
        iteration = final_state.get("iterations", 0)
        errors = final_state.get("errors")

        _sessions[session_id].update(
            status=status,
            iteration=iteration,
            errors=errors,
        )
        await _broadcast(session_id, {
            "event": "completed",
            "status": status,
            "iteration": iteration,
        })
        logger.info("Session %s finished: status=%s, iterations=%d", session_id, status, iteration)

    except Exception as exc:
        error_msg = str(exc)
        _sessions[session_id].update(status="failed", errors=error_msg)
        await _broadcast(session_id, {"event": "error", "detail": error_msg})
        logger.exception("Pipeline error for session %s", session_id)


async def _run_project_pipeline_async(
    requirements: str,
    session_id: str,
    project_dir: str,
    max_iterations: int,
    evolutions: int,
) -> None:
    """Run the project mode pipeline in a thread and broadcast progress."""
    from graph.project_pipeline import run_project_pipeline

    _sessions[session_id]["status"] = "running"
    await _broadcast(session_id, {"event": "started", "session_id": session_id, "mode": "project"})

    loop = asyncio.get_running_loop()

    # Create callback to broadcast node events
    def node_callback(node_name: str, state: dict):
        """Broadcast node_enter events for frontend visualization."""
        asyncio.run_coroutine_threadsafe(
            _broadcast(session_id, {
                "event": "node_enter",
                "node": node_name,
                "agent": node_name,
                "iteration": state.get("iteration", 0),
            }),
            loop
        )

    try:
        final_state = await loop.run_in_executor(
            None,
            lambda: run_project_pipeline(
                requirements=requirements,
                project_dir=project_dir,
                max_iterations=max_iterations,
                evolutions=evolutions,
                node_callback=node_callback,
            ),
        )
        status = final_state.get("status", "failed")
        files = final_state.get("files", [])

        _sessions[session_id].update(
            status=status,
            files=files,
        )
        await _broadcast(session_id, {
            "event": "completed",
            "status": status,
            "files": files,
        })
        logger.info("Project session %s finished: status=%s, files=%d", session_id, status, len(files))

    except Exception as exc:
        error_msg = str(exc)
        _sessions[session_id].update(status="failed", errors=error_msg)
        await _broadcast(session_id, {"event": "error", "detail": error_msg})
        logger.exception("Project pipeline error for session %s", session_id)


# ── REST Endpoints ────────────────────────────────────────────────────────────

@router.post(
    "/run-task",
    response_model=RunTaskResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Start a new Lua generation pipeline",
)
async def run_task(body: RunTaskRequest):
    from config.loader import load_settings
    settings = load_settings()
    max_iterations = body.max_iterations or settings["pipeline"]["max_iterations"]

    workspace = _get_workspace_dir()

    # Create session directory based on mode
    if body.mode == "project":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"project_{timestamp}"
        session_path = workspace / session_id
    else:
        session_id, session_path = _make_session_dir(workspace)

    session_path.mkdir(parents=True, exist_ok=True)

    # Persist task description
    (session_path / "task.txt").write_text(body.task, encoding="utf-8")

    # Register session
    _sessions[session_id] = {
        "status": "running",
        "task": body.task,
        "mode": body.mode,
        "iteration": 0,
        "errors": None,
        "ws_clients": [],
    }

    # Fire-and-forget pipeline execution
    if body.mode == "project":
        asyncio.create_task(
            _run_project_pipeline_async(
                body.task, session_id, str(session_path),
                max_iterations, body.evolutions
            )
        )
    else:
        asyncio.create_task(
            _run_pipeline_async(body.task, session_id, str(session_path), max_iterations)
        )

    logger.info("Started %s session %s for task: %s", body.mode, session_id, body.task[:80])
    return RunTaskResponse(
        session_id=session_id,
        status="running",
        message=f"{body.mode.capitalize()} pipeline started",
    )


@router.get(
    "/session/{session_id}",
    response_model=SessionStatus,
    responses={404: {"model": ErrorResponse}},
    summary="Get session status",
)
async def get_session(session_id: str):
    path = _session_path(session_id)
    iteration = _detect_iteration(path)
    has_final = (path / "final.lua").exists()

    # Read task
    task_file = path / "task.txt"
    task = task_file.read_text(encoding="utf-8").strip() if task_file.exists() else None

    # Merge in-memory status with filesystem state
    mem = _sessions.get(session_id, {})
    status = mem.get("status", "done" if has_final else "unknown")
    errors = mem.get("errors")

    # If no in-memory record, try to detect errors from latest iteration
    if errors is None:
        error_files = sorted(path.glob("iteration_*_errors.txt"))
        if error_files:
            errors = error_files[-1].read_text(encoding="utf-8").strip() or None

    return SessionStatus(
        session_id=session_id,
        status=status,
        task=task,
        iteration=iteration,
        errors=errors,
        has_final=has_final,
    )


@router.get(
    "/sessions",
    response_model=list[SessionListItem],
    summary="List all workspace sessions",
)
async def list_sessions():
    workspace = _get_workspace_dir()
    if not workspace.exists():
        return []

    items: list[SessionListItem] = []
    # Sort by modification time (newest first) instead of name
    entries = sorted(workspace.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for entry in entries:
        if not entry.is_dir():
            continue
        # Include both session_* and project_* directories
        if not (entry.name.startswith("session_") or entry.name.startswith("project_")):
            continue
        task_file = entry / "task.txt"
        requirements_file = entry / "requirements.md"

        # Try task.txt first, then requirements.md for project mode
        if task_file.exists():
            task = task_file.read_text(encoding="utf-8").strip()
        elif requirements_file.exists():
            task = requirements_file.read_text(encoding="utf-8").strip()
        else:
            task = None

        # For project mode, check multiple completion indicators
        # For quick mode, check final.lua
        is_project = entry.name.startswith("project_")
        if is_project:
            # Project is complete if it has README.md, manifest.json, or any files in src/
            has_final = (
                (entry / "README.md").exists() or
                (entry / "manifest.json").exists() or
                any((entry / "src").glob("*.lua")) if (entry / "src").exists() else False
            )
        else:
            has_final = (entry / "final.lua").exists()

        items.append(SessionListItem(session_id=entry.name, task=task, has_final=has_final))

    return items


@router.get(
    "/session/{session_id}/files",
    response_model=list[SessionFile],
    responses={404: {"model": ErrorResponse}},
    summary="List files in a session folder",
)
async def list_session_files(session_id: str):
    path = _session_path(session_id)
    return [
        SessionFile(name=f.name, size=f.stat().st_size)
        for f in sorted(path.iterdir())
        if f.is_file()
    ]


@router.get(
    "/session/{session_id}/final",
    responses={404: {"model": ErrorResponse}},
    summary="Return final.lua content",
)
async def get_final_lua(session_id: str):
    path = _session_path(session_id)
    final = path / "final.lua"
    if not final.exists():
        raise HTTPException(status_code=404, detail="final.lua not found — pipeline may still be running")
    return {"content": final.read_text(encoding="utf-8")}


@router.get(
    "/session/{session_id}/file/{filename}",
    responses={404: {"model": ErrorResponse}},
    summary="Return content of any file in the session folder",
)
async def get_session_file(session_id: str, filename: str):
    path = _session_path(session_id)
    # Prevent path traversal
    target = (path / filename).resolve()
    if not str(target).startswith(str(path.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return {"filename": filename, "content": target.read_text(encoding="utf-8")}


# ── WebSocket Endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    Live updates for a running session.
    Client connects and receives JSON events: started, progress, completed, error.
    """
    await websocket.accept()
    logger.info("WebSocket connected for session %s", session_id)

    # Register client
    if session_id not in _sessions:
        _sessions[session_id] = {
            "status": "unknown",
            "task": None,
            "iteration": 0,
            "errors": None,
            "ws_clients": [],
        }
    _sessions[session_id]["ws_clients"].append(websocket)

    try:
        # Send current status immediately
        path = _get_workspace_dir() / session_id
        if path.is_dir():
            iteration = _detect_iteration(path)
            has_final = (path / "final.lua").exists()
            await websocket.send_text(json.dumps({
                "event": "status",
                "iteration": iteration,
                "has_final": has_final,
                "status": _sessions[session_id].get("status", "unknown"),
            }))

        # Keep connection alive — wait for client disconnect
        while True:
            # Periodically push iteration updates
            await asyncio.sleep(2)
            if path.is_dir():
                new_iter = _detect_iteration(path)
                new_final = (path / "final.lua").exists()
                await websocket.send_text(json.dumps({
                    "event": "progress",
                    "iteration": new_iter,
                    "has_final": new_final,
                    "status": _sessions.get(session_id, {}).get("status", "unknown"),
                }))
                # Stop polling once done
                if _sessions.get(session_id, {}).get("status") in ("done", "failed"):
                    await websocket.send_text(json.dumps({
                        "event": "finished",
                        "status": _sessions[session_id]["status"],
                    }))
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    finally:
        clients = _sessions.get(session_id, {}).get("ws_clients", [])
        if websocket in clients:
            clients.remove(websocket)
