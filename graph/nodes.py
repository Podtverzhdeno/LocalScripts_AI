"""
LangGraph node functions — pure functions that transform AgentState.
LLM injected via closure from pipeline.py — avoids re-initializing on every call
and makes mocking in tests trivial.
"""

import os
from pathlib import Path
from langchain_core.language_models import BaseChatModel
from graph.state import AgentState
from tools.lua_runner import LuaRunner
from config.loader import load_settings


def _get_runner(state: AgentState) -> LuaRunner:
    settings = load_settings()
    pipeline_cfg = settings["pipeline"]
    timeout = pipeline_cfg.get("execution_timeout", 10)

    # Get sandbox mode from env (CLI override) or settings
    sandbox_mode = os.getenv("SANDBOX_MODE", pipeline_cfg.get("sandbox_mode", "lua"))

    return LuaRunner(session_dir=state["session_dir"], timeout=timeout, sandbox=sandbox_mode)


def make_nodes(
    llm: BaseChatModel | None = None,
    *,
    llm_generator: BaseChatModel | None = None,
    llm_validator: BaseChatModel | None = None,
    llm_reviewer: BaseChatModel | None = None,
    node_callback=None,
    code_callback=None,
):
    """
    Factory that returns node functions with LLM injected via closure.

    Supports per-agent LLM overrides for hybrid pipelines:
        - llm_generator: model for code generation (default: llm)
        - llm_validator: model for error explanation (default: llm)
        - llm_reviewer:  model for code review (default: llm)

    If a per-agent LLM is not provided, falls back to the shared `llm`.
    """
    from agents.generator import GeneratorAgent
    from agents.validator import ValidatorAgent
    from agents.reviewer import ReviewerAgent

    _gen_llm = llm_generator or llm
    _val_llm = llm_validator or llm
    _rev_llm = llm_reviewer or llm

    def node_generate(state: AgentState) -> dict:
        """Generator node — writes or fixes Lua code."""
        if node_callback:
            node_callback("generate", state)
        agent = GeneratorAgent(_gen_llm)
        code = agent.generate(
            task=state["task"],
            errors=state.get("errors"),
            review=state.get("review"),
        )
        iteration = state["iterations"] + 1
        runner = _get_runner(state)
        runner.save_iteration(code, iteration)
        print(f"\n[Generator] Iteration {iteration} — {len(code)} chars written")

        # Stream code to frontend if callback provided
        if code_callback:
            code_callback(code, "generate")

        return {
            "code": code,
            "iterations": iteration,
            "errors": None,
            "review": None,
            "status": "validating",
        }

    def node_validate(state: AgentState) -> dict:
        """Validator node — runs luac + lua, explains errors via LLM."""
        if node_callback:
            node_callback("validate", state)
        runner = _get_runner(state)
        agent = ValidatorAgent(_val_llm, runner)
        is_valid, error_explanation = agent.validate(
            code=state["code"],
            task=state["task"],
            iteration=state["iterations"],
        )

        # Get profiling metrics from last execution
        profile_metrics = None
        if hasattr(agent, '_last_result') and agent._last_result:
            result = agent._last_result
            if result.execution_time > 0:
                print(f"[Validator] Performance: {result.execution_time:.3f}s, {result.memory_used}KB")
                profile_metrics = {
                    "time": result.execution_time,
                    "memory": result.memory_used
                }

        if is_valid:
            print(f"[Validator] OK - Code valid")
            return {"errors": None, "status": "reviewing", "profile_metrics": profile_metrics}
        else:
            print(f"[Validator] ERROR - Retrying")
            return {"errors": error_explanation, "status": "generating"}

    def node_review(state: AgentState) -> dict:
        """Reviewer node — quality check, may request improvements."""
        if node_callback:
            node_callback("review", state)
        agent = ReviewerAgent(_rev_llm)
        is_done, feedback = agent.review(
            code=state["code"],
            task=state["task"],
            profile_metrics=state.get("profile_metrics"),
        )
        if is_done:
            print("[Reviewer] APPROVED")
            _save_final({**state, "status": "done"}, feedback)
            return {"review": feedback, "status": "done"}
        else:
            print(f"[Reviewer] Improvements requested")
            return {"review": feedback, "status": "generating"}
            return {"review": feedback, "status": "generating"}

    def node_fail(state: AgentState) -> dict:
        """Terminal failure — max iterations reached."""
        if node_callback:
            node_callback("fail", state)
        print(f"\n[Pipeline] Max iterations ({state['max_iterations']}) reached.")
        _save_final(state, "Max iterations reached — partial result saved.")
        return {"status": "failed"}

    return node_generate, node_validate, node_review, node_fail


def _save_final(state: AgentState, review_text: str) -> None:
    session = Path(state["session_dir"])
    if state.get("code"):
        (session / "final.lua").write_text(state["code"], encoding="utf-8")

    # Build report with profiling metrics
    report = f"# LocalScript Report\n\n## Task\n{state['task']}\n\n"
    report += f"## Iterations\n{state['iterations']}\n\n"
    report += f"## Status\n{state['status']}\n\n"

    # Add profiling metrics if available
    if state.get("profile_metrics"):
        metrics = state["profile_metrics"]
        report += f"## Performance\n"
        report += f"- Execution time: {metrics.get('time', 0):.3f}s\n"
        report += f"- Memory used: {metrics.get('memory', 0)}KB\n\n"

    report += f"## Review\n{review_text}\n"
    (session / "report.md").write_text(report, encoding="utf-8")
    print(f"[Pipeline] Saved to: {session}")
