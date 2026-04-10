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
    llm_test_generator: BaseChatModel | None = None,
    llm_retriever: BaseChatModel | None = None,
    llm_approver: BaseChatModel | None = None,
    llm_clarifier: BaseChatModel | None = None,
    llm_checkpoint: BaseChatModel | None = None,
    rag_system=None,
    node_callback=None,
    code_callback=None,
    use_rag_workflow=True,
):
    """
    Factory that returns node functions with LLM injected via closure.

    Supports per-agent LLM overrides for hybrid pipelines:
        - llm_generator: model for code generation (default: llm)
        - llm_validator: model for error explanation (default: llm)
        - llm_reviewer:  model for code review (default: llm)
        - llm_test_generator: model for test case generation (default: llm)
        - llm_retriever: model for RAG search (default: llm)
        - llm_approver: model for RAG approval (default: llm)
        - llm_clarifier: model for task clarification (default: llm)
        - llm_checkpoint: model for checkpoint coordination (default: llm)
        - rag_system: RAG system for retrieval-augmented generation
        - use_rag_workflow: Enable new RAG workflow with retriever+approver agents
        - node_callback: Callback for real-time progress updates
        - code_callback: Callback for streaming code generation

    If a per-agent LLM is not provided, falls back to the shared `llm`.
    """
    from agents.generator import GeneratorAgent
    from agents.validator import ValidatorAgent
    from agents.reviewer import ReviewerAgent
    from agents.test_generator import TestGeneratorAgent
    from agents.retriever import RetrieverAgent
    from agents.approver import ApproverAgent
    from agents.clarifier import ClarifierAgent
    from agents.checkpoint import CheckpointAgent

    _gen_llm = llm_generator or llm
    _val_llm = llm_validator or llm
    _rev_llm = llm_reviewer or llm
    _test_llm = llm_test_generator or llm
    _ret_llm = llm_retriever or llm
    _app_llm = llm_approver or llm
    _clar_llm = llm_clarifier or llm
    _check_llm = llm_checkpoint or llm

    def node_generate(state: AgentState) -> dict:
        """Generator node — writes or fixes Lua code."""
        if node_callback:
            node_callback("generate", state)

        # Get approved template from state if available
        approved_template = state.get("approved_template")

        agent = GeneratorAgent(_gen_llm, rag_system=rag_system)
        code = agent.generate(
            task=state["task"],
            errors=state.get("errors"),
            review=state.get("review"),
            approved_template=approved_template,
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

    def node_rag_retrieve(state: AgentState) -> dict:
        """RAG Retriever node — searches knowledge base for relevant examples."""
        if node_callback:
            node_callback("rag_retrieve", state)

        if not rag_system or not use_rag_workflow:
            print("[RAG] Workflow disabled, skipping retrieval")
            return {"rag_results": None, "status": "generating"}

        # Check cache first
        from rag.cache import get_rag_cache
        from config.loader import load_settings

        settings = load_settings()
        rag_config = settings.get("rag", {})
        cache_enabled = rag_config.get("cache_enabled", True)

        if cache_enabled:
            cache = get_rag_cache(
                max_size=rag_config.get("cache_max_size", 100),
                ttl_seconds=None  # No expiration by default
            )

            cached_result = cache.get(state["task"])
            if cached_result:
                print("[RAG] ✓ Using cached results (skipping retrieval + approval)")
                return cached_result

        print("\n[RAG] Starting retrieval workflow...")
        retriever = RetrieverAgent(_ret_llm, rag_system=rag_system)

        # Get retrieval_k from config (default: 3 for 7B models)
        retrieval_k = rag_config.get("retrieval_k", 3)
        results = retriever.search(task=state["task"], k=retrieval_k)

        if not results:
            print("[RAG] No examples found, proceeding without template")
            return {"rag_results": None, "approved_template": None, "status": "generating"}

        # Format for approver
        formatted_examples = retriever.format_examples_for_approval(results)

        return {
            "rag_results": results,
            "rag_formatted": formatted_examples,
            "status": "rag_approving",
        }

    def node_rag_approve(state: AgentState) -> dict:
        """RAG Approver node — evaluates relevance of retrieved examples."""
        if node_callback:
            node_callback("rag_approve", state)

        rag_results = state.get("rag_results")
        rag_formatted = state.get("rag_formatted")

        if not rag_results or not rag_formatted:
            print("[RAG] No results to approve")
            return {"approved_template": None, "status": "generating"}

        # Check if we should skip approval (for debugging or if Approver is slow)
        import os
        skip_approval = os.getenv("RAG_SKIP_APPROVAL", "false").lower() == "true"

        if skip_approval:
            print("[RAG] ⚠️  Skipping approval (RAG_SKIP_APPROVAL=true)")
            print("[RAG] Using all retrieved examples as template")
            # Use all examples without approval
            if rag_system:
                approved_template = rag_system.format_context(
                    [doc for doc, _ in rag_results],
                    max_length=2000
                )
            else:
                approved_template = rag_formatted

            return {
                "approved_template": approved_template,
                "rag_decision": {
                    "approved": True,
                    "reason": "Approval skipped (RAG_SKIP_APPROVAL=true)",
                    "selected_examples": list(range(1, len(rag_results) + 1)),
                    "confidence": 1.0
                },
                "status": "generating",
            }

        print("\n[RAG] Evaluating retrieved examples...")
        approver = ApproverAgent(_app_llm)

        # Get cache instance for storing results
        from rag.cache import get_rag_cache
        from config.loader import load_settings

        settings = load_settings()
        rag_config = settings.get("rag", {})
        cache_enabled = rag_config.get("cache_enabled", True)
        cache = get_rag_cache() if cache_enabled else None

        try:
            # Evaluate relevance with timeout protection
            decision = approver.evaluate(
                task=state["task"],
                retrieved_examples=rag_formatted,
            )

            if decision["approved"] and decision["selected_examples"]:
                # Extract approved examples
                approved_docs = approver.extract_approved_examples(
                    rag_results,
                    decision["selected_examples"]
                )

                # Format approved examples as template
                if rag_system:
                    approved_template = rag_system.format_context(
                        [doc for doc, _ in approved_docs],
                        max_length=2000
                    )
                else:
                    approved_template = rag_formatted

                print(f"[RAG] ✓ APPROVED - Using {len(decision['selected_examples'])} example(s) as template")

                # Cache the result for future similar tasks
                if cache_enabled:
                    cache_data = {
                        "rag_results": rag_results,
                        "rag_formatted": rag_formatted,
                        "approved_template": approved_template,
                        "rag_decision": decision,
                        "status": "generating",
                    }
                    cache.set(state["task"], cache_data)
                    print("[RAG] ✓ Result cached for future use")

                return {
                    "approved_template": approved_template,
                    "rag_decision": decision,
                    "status": "generating",
                }
            else:
                print(f"[RAG] ✗ REJECTED - {decision['reason']}")
                print("[RAG] Generating from scratch")

                # Cache rejection result too (avoid re-evaluating same task)
                if cache_enabled:
                    cache_data = {
                        "rag_results": rag_results,
                        "rag_formatted": rag_formatted,
                        "approved_template": None,
                        "rag_decision": decision,
                        "status": "generating",
                    }
                    cache.set(state["task"], cache_data)
                    print("[RAG] ✓ Rejection cached (won't re-evaluate)")

                return {
                    "approved_template": None,
                    "rag_decision": decision,
                    "status": "generating",
                }
        except Exception as e:
            print(f"[RAG] ⚠️  Approval failed: {e}")
            print("[RAG] Falling back to generation without template")
            return {
                "approved_template": None,
                "rag_decision": {
                    "approved": False,
                    "reason": f"Approval error: {str(e)}",
                    "selected_examples": [],
                    "confidence": 0.0
                },
                "status": "generating",
            }

    def node_validate(state: AgentState) -> dict:
        """Validator node — runs luac + lua with functional tests, explains errors via LLM."""
        if node_callback:
            node_callback("validate", state)
        runner = _get_runner(state)
        agent = ValidatorAgent(_val_llm, runner)

        # Generate functional test cases on first iteration
        test_code = state.get("test_code")
        if not test_code and state["iterations"] == 1:
            print("[Validator] Generating functional test cases...")
            test_agent = TestGeneratorAgent(_test_llm)
            test_code = test_agent.generate_tests(
                task=state["task"],
                code=state["code"]
            )
            # Save test cases to session
            test_path = Path(state["session_dir"]) / "test_cases.lua"
            test_path.write_text(test_code, encoding="utf-8")
            print(f"[Validator] Generated {len(test_code)} chars of test cases")

            # Stream test code generation
            if code_callback:
                code_callback(test_code, "test_generator")

        # Run validation with functional tests
        if test_code:
            is_valid, error_explanation, test_results = agent.validate_with_tests(
                code=state["code"],
                test_code=test_code,
                task=state["task"],
                iteration=state["iterations"],
            )
            print(f"[Validator] Tests: {test_results['passed']}/{test_results['total']} passed")

            # Stream error explanation if validation failed
            if not is_valid and error_explanation and code_callback:
                code_callback(error_explanation, "validator")
        else:
            # Fallback to basic validation (backward compatibility)
            is_valid, error_explanation = agent.validate(
                code=state["code"],
                task=state["task"],
                iteration=state["iterations"],
            )
            test_results = None

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
            return {
                "errors": None,
                "status": "reviewing",
                "profile_metrics": profile_metrics,
                "test_code": test_code,
                "test_results": test_results
            }
        else:
            print(f"[Validator] ERROR - Retrying")
            return {
                "errors": error_explanation,
                "status": "generating",
                "test_code": test_code,
                "test_results": test_results
            }

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

        # Stream feedback if improvements requested
        if not is_done and feedback and code_callback:
            code_callback(feedback, "reviewer")
        if is_done:
            print("[Reviewer] APPROVED")
            _save_final({**state, "status": "done"}, feedback)
            return {"review": feedback, "status": "done"}
        else:
            print(f"[Reviewer] Improvements requested")
            return {"review": feedback, "status": "generating"}

    def node_fail(state: AgentState) -> dict:
        """Terminal failure — max iterations reached."""
        if node_callback:
            node_callback("fail", state)
        print(f"\n[Pipeline] Max iterations ({state['max_iterations']}) reached.")
        _save_final(state, "Max iterations reached — partial result saved.")
        return {"status": "failed"}

    def node_clarify(state: AgentState) -> dict:
        """Clarifier node — analyzes task for ambiguities and asks questions."""
        if node_callback:
            node_callback("clarify", state)

        # Skip if already attempted clarification (avoid loops)
        if state.get("clarification_attempted", False):
            print("[Clarifier] Already attempted, skipping")
            return {"needs_clarification": False}

        agent = ClarifierAgent(_clar_llm)
        questions = agent.analyze_task(state["task"])

        if questions:
            print(f"[Clarifier] Generated {len(questions)} question(s)")
            # Broadcast questions to frontend via WebSocket
            if node_callback:
                import asyncio
                asyncio.create_task(_broadcast_clarification(state.get("session_id"), questions))

            return {
                "clarification_questions": questions,
                "needs_clarification": True,
                "clarification_attempted": True,
                "status": "clarifying",
            }
        else:
            print("[Clarifier] Task is clear, no questions needed")
            return {
                "needs_clarification": False,
                "clarification_attempted": True,
            }

    def node_enrich_task(state: AgentState) -> dict:
        """Enrich task with user answers from clarification."""
        if node_callback:
            node_callback("enrich_task", state)

        questions = state.get("clarification_questions", [])
        answers = state.get("user_answers", {})

        if not questions or not answers:
            print("[Clarifier] No answers to process")
            return {}

        agent = ClarifierAgent(_clar_llm)
        enriched_task = agent.enrich_task_with_answers(
            state["task"],
            questions,
            answers
        )

        print(f"[Clarifier] Task enriched with {len(answers)} answer(s)")

        return {
            "task": enriched_task,
            "needs_clarification": False,
        }

    def node_checkpoint(state: AgentState) -> dict:
        """Checkpoint node — presents code for user approval."""
        if node_callback:
            node_callback("checkpoint", state)

        agent = CheckpointAgent(_check_llm)

        # Check if checkpoint is needed
        if not agent.should_checkpoint(state["iterations"], state["status"] == "reviewing"):
            return {}

        # Prepare checkpoint data for frontend
        checkpoint_data = agent.prepare_checkpoint_data(state)

        print(f"[Checkpoint] Code ready for review (iteration {state['iterations']})")

        # Broadcast checkpoint to frontend
        if node_callback:
            import asyncio
            asyncio.create_task(_broadcast_checkpoint(state.get("session_id"), checkpoint_data))

        return {
            "checkpoint_pending": True,
            "status": "awaiting_approval",
        }

    def node_process_checkpoint(state: AgentState) -> dict:
        """Process user's checkpoint decision."""
        if node_callback:
            node_callback("process_checkpoint", state)

        action = state.get("checkpoint_action")
        agent = CheckpointAgent(_check_llm)

        if action == "approve":
            print("[Checkpoint] User approved, continuing to review")
            return {
                "checkpoint_pending": False,
                "status": "reviewing",
            }

        elif action == "reject":
            feedback = state.get("user_feedback", "")
            enriched_task = agent.process_user_feedback(feedback, state["task"])
            print(f"[Checkpoint] User requested changes: {feedback[:50]}...")
            return {
                "task": enriched_task,
                "checkpoint_pending": False,
                "status": "generating",
                "review": feedback,  # Use feedback as review
            }

        elif action == "alternatives":
            print("[Checkpoint] Generating alternatives...")
            alternatives = agent.generate_alternatives(
                state["task"],
                state["code"],
                count=2
            )

            # Broadcast alternatives to frontend
            session_id = state.get("session_id")
            if session_id:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(_broadcast_alternatives(session_id, alternatives))
                except Exception as e:
                    print(f"[Checkpoint] Failed to broadcast alternatives: {e}")

            return {
                "alternatives": alternatives,
                "status": "selecting_alternative",
            }

        elif action == "save_to_kb":
            print("[Checkpoint] User approved + saving to knowledge base")
            # Prepare for RAG storage
            kb_data = agent.prepare_for_knowledge_base(state)

            # Save to RAG if available
            if rag_system:
                try:
                    _save_to_knowledge_base(rag_system, kb_data)
                    print("[Checkpoint] ✓ Saved to knowledge base")
                except Exception as e:
                    print(f"[Checkpoint] Failed to save to KB: {e}")

            return {
                "checkpoint_pending": False,
                "save_to_knowledge_base": True,
                "status": "reviewing",
            }

        return {}

    def node_clarify_errors(state: AgentState) -> dict:
        """Clarifier node after repeated validation failures."""
        if node_callback:
            node_callback("clarify_errors", state)

        # Only trigger after 2+ failed iterations
        if state["iterations"] < 2:
            return {"needs_clarification": False}

        # Skip if already attempted
        if state.get("clarification_attempted", False):
            return {"needs_clarification": False}

        errors = state.get("errors", "")
        task = state.get("task", "")

        # Simple heuristic: check for common sandbox errors
        needs_clarification = any(keyword in errors.lower() for keyword in [
            "sandbox", "io.open", "require", "module", "not found"
        ])

        if needs_clarification:
            print("[Clarifier] Detected sandbox/dependency issues, asking user")

            # Generate contextual question based on error
            question = {
                "question": "Code failed due to sandbox restrictions. How should I proceed?",
                "options": [
                    "Use in-memory data structures (recommended)",
                    "Change task requirements",
                    "Continue trying"
                ],
                "required": True
            }

            return {
                "clarification_questions": [question],
                "needs_clarification": True,
                "clarification_attempted": True,
                "status": "clarifying_errors",
            }

        return {"needs_clarification": False}

    return (node_generate, node_validate, node_review, node_fail,
            node_rag_retrieve, node_rag_approve, node_clarify,
            node_enrich_task, node_checkpoint, node_process_checkpoint,
            node_clarify_errors)


def _save_final(state: AgentState, review_text: str) -> None:
    session = Path(state["session_dir"])
    if state.get("code"):
        (session / "final.lua").write_text(state["code"], encoding="utf-8")

    # Build report with profiling metrics and test results
    report = f"# LocalScript Report\n\n## Task\n{state['task']}\n\n"
    report += f"## Iterations\n{state['iterations']}\n\n"
    report += f"## Status\n{state['status']}\n\n"

    # Add test results if available
    if state.get("test_results"):
        results = state["test_results"]
        report += f"## Functional Tests\n"
        report += f"- Total: {results['total']}\n"
        report += f"- Passed: {results['passed']}\n"
        report += f"- Failed: {results['failed']}\n"
        if results['passed'] == results['total']:
            report += f"- Status: ✅ All tests passed\n\n"
        else:
            report += f"- Status: ❌ Some tests failed\n\n"

    # Add profiling metrics if available
    if state.get("profile_metrics"):
        metrics = state["profile_metrics"]
        report += f"## Performance\n"
        report += f"- Execution time: {metrics.get('time', 0):.3f}s\n"
        report += f"- Memory used: {metrics.get('memory', 0)}KB\n\n"

    report += f"## Review\n{review_text}\n"
    (session / "report.md").write_text(report, encoding="utf-8")
    print(f"[Pipeline] Saved to: {session}")


async def _broadcast_clarification(session_id: str, questions: list) -> None:
    """Broadcast clarification questions to frontend via WebSocket."""
    try:
        from api.routes import _broadcast
        await _broadcast(session_id, {
            "event": "clarification_required",
            "questions": questions,
        })
    except Exception as e:
        import logging
        logging.getLogger("localscript.graph").warning(f"Failed to broadcast clarification: {e}")


async def _broadcast_checkpoint(session_id: str, checkpoint_data: dict) -> None:
    """Broadcast checkpoint to frontend via WebSocket."""
    try:
        from api.routes import _broadcast
        await _broadcast(session_id, {
            "event": "checkpoint_required",
            "data": checkpoint_data,
        })
    except Exception as e:
        import logging
        logging.getLogger("localscript.graph").warning(f"Failed to broadcast checkpoint: {e}")


async def _broadcast_alternatives(session_id: str, alternatives: list) -> None:
    """Broadcast generated alternatives to frontend via WebSocket."""
    try:
        from api.routes import _broadcast
        await _broadcast(session_id, {
            "event": "alternatives_ready",
            "data": {"alternatives": alternatives},
        })
    except Exception as e:
        import logging
        logging.getLogger("localscript.graph").warning(f"Failed to broadcast alternatives: {e}")


def _save_to_knowledge_base(rag_system, kb_data: dict) -> None:
    """Save approved code to RAG knowledge base."""
    import logging
    logger = logging.getLogger("localscript.graph")

    try:
        # Format document for RAG
        document = f"""# {kb_data['task']}

Tags: {', '.join(kb_data['tags'])}
User Approved: Yes
Quality Score: {kb_data['quality_score']:.2f}

## Code
```lua
{kb_data['code']}
```

## Metadata
- Test Results: {kb_data['test_results'].get('passed', 0)}/{kb_data['test_results'].get('total', 0)} passed
- Performance: {kb_data['profile_metrics'].get('time', 0):.3f}s
"""

        # Add to RAG collection
        metadata = {
            "task": kb_data["task"],
            "tags": kb_data["tags"],
            "user_approved": True,
            "quality_score": kb_data["quality_score"],
            "test_pass_rate": kb_data["test_results"].get("passed", 0) / max(kb_data["test_results"].get("total", 1), 1),
            "execution_time": kb_data["profile_metrics"].get("time", 0),
        }

        # Use RAG system's add method
        rag_system.add_documents(
            documents=[document],
            metadatas=[metadata],
            ids=[f"user_approved_{hash(kb_data['task'])}"]
        )

        logger.info(f"[RAG] Saved approved code to knowledge base: {kb_data['task'][:50]}...")

    except Exception as e:
        logger.error(f"[RAG] Failed to save to knowledge base: {e}")
        raise
