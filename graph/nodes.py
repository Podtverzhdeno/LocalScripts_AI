"""
LangGraph node functions — pure functions that transform AgentState.
LLM injected via closure from pipeline.py — avoids re-initializing on every call
and makes mocking in tests trivial.
"""

from pathlib import Path
from langchain_core.language_models import BaseChatModel
from graph.state import AgentState
from tools.lua_runner import LuaRunner
from config.loader import load_settings


def _get_runner(state: AgentState) -> LuaRunner:
    settings = load_settings()
    timeout = settings["pipeline"].get("execution_timeout", 10)
    return LuaRunner(session_dir=state["session_dir"], timeout=timeout)


def make_nodes(llm: BaseChatModel):
    """
    Factory that returns node functions with LLM injected via closure.
    Called once in pipeline.py — clean dependency injection.
    """
    from agents.generator import GeneratorAgent
    from agents.validator import ValidatorAgent
    from agents.reviewer import ReviewerAgent

    def node_generate(state: AgentState) -> dict:
        """Generator node — writes or fixes Lua code."""
        agent = GeneratorAgent(llm)
        code = agent.generate(
            task=state["task"],
            errors=state.get("errors"),
            review=state.get("review"),
        )
        iteration = state["iterations"] + 1
        runner = _get_runner(state)
        runner.save_iteration(code, iteration)
        print(f"\n[Generator] Iteration {iteration} — {len(code)} chars written")
        return {
            "code": code,
            "iterations": iteration,
            "errors": None,
            "review": None,
            "status": "validating",
        }

    def node_validate(state: AgentState) -> dict:
        """Validator node — runs luac + lua, explains errors via LLM."""
        runner = _get_runner(state)
        agent = ValidatorAgent(llm, runner)
        is_valid, error_explanation = agent.validate(
            code=state["code"],
            task=state["task"],
            iteration=state["iterations"],
        )
        if is_valid:
            print(f"[Validator] ✓ Code OK")
            return {"errors": None, "status": "reviewing"}
        else:
            print(f"[Validator] ✗ Errors — retrying")
            return {"errors": error_explanation, "status": "generating"}

    def node_review(state: AgentState) -> dict:
        """Reviewer node — quality check, may request improvements."""
        agent = ReviewerAgent(llm)
        is_done, feedback = agent.review(
            code=state["code"],
            task=state["task"],
        )
        if is_done:
            print("[Reviewer] ✓ Approved")
            _save_final({**state, "status": "done"}, feedback)
            return {"review": feedback, "status": "done"}
        else:
            print(f"[Reviewer] → Improvements requested")
            return {"review": feedback, "status": "generating"}

    def node_fail(state: AgentState) -> dict:
        """Terminal failure — max iterations reached."""
        print(f"\n[Pipeline] Max iterations ({state['max_iterations']}) reached.")
        _save_final(state, "Max iterations reached — partial result saved.")
        return {"status": "failed"}

    return node_generate, node_validate, node_review, node_fail


def _save_final(state: AgentState, review_text: str) -> None:
    session = Path(state["session_dir"])
    if state.get("code"):
        (session / "final.lua").write_text(state["code"], encoding="utf-8")
    report = f"# LocalScript Report\n\n## Task\n{state['task']}\n\n"
    report += f"## Iterations\n{state['iterations']}\n\n"
    report += f"## Status\n{state['status']}\n\n"
    report += f"## Review\n{review_text}\n"
    (session / "report.md").write_text(report, encoding="utf-8")
    print(f"[Pipeline] Saved to: {session}")
