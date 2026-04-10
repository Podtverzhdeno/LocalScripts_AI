"""
Упрощённый тест без Clarifier и RAG - только базовый pipeline
"""
import os
os.environ["RAG_ENABLED"] = "false"
os.environ["GENERATOR_STRATEGY"] = "none"

from graph.pipeline import build_pipeline
from llm.factory import get_llm
from pathlib import Path
from datetime import datetime

# Создаём сессию
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = Path("workspace") / f"test_{timestamp}"
session_dir.mkdir(parents=True, exist_ok=True)

# Задача
task = "Напиши функцию sum_array(arr), которая вычисляет сумму всех элементов массива"

print(f"\n{'='*60}")
print(f"  Тест LocalScript (упрощённый)")
print(f"{'='*60}")
print(f"  Задача: {task}")
print(f"  Сессия: {session_dir}")
print(f"{'='*60}\n")

# Получаем LLM
llm = get_llm()

# Строим упрощённый pipeline БЕЗ Clarifier
from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from graph.nodes import make_nodes

# Создаём ноды
(node_generate, node_validate, node_review, node_fail,
 node_rag_retrieve, node_rag_approve, node_clarify,
 node_enrich_task, node_checkpoint, node_process_checkpoint,
 node_clarify_errors) = make_nodes(
    llm,
    rag_system=None,
    use_rag_workflow=False,
    node_callback=None,
    code_callback=None,
)

# Строим граф БЕЗ Clarifier
graph = StateGraph(AgentState)
graph.add_node("generate", node_generate)
graph.add_node("validate", node_validate)
graph.add_node("review", node_review)
graph.add_node("fail", node_fail)

# Простой flow: START → generate → validate → review → END
graph.add_edge(START, "generate")
graph.add_edge("generate", "validate")

def should_retry_or_fail(state: AgentState) -> str:
    if state["iterations"] >= state["max_iterations"]:
        return "fail"
    if state["status"] == "generating":
        return "generate"
    return "review"

def review_done_or_retry(state: AgentState) -> str:
    if state["status"] == "done":
        return END
    if state["iterations"] >= state["max_iterations"]:
        return "fail"
    return "generate"

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

# Компилируем
pipeline = graph.compile()

# Запускаем
initial_state: AgentState = {
    "task": task,
    "code": None,
    "errors": None,
    "review": None,
    "test_code": None,
    "test_results": None,
    "iterations": 0,
    "max_iterations": 2,
    "status": "generating",
    "session_dir": str(session_dir),
    "profile_metrics": None,
    "messages": [],
    "rag_results": None,
    "rag_formatted": None,
    "rag_decision": None,
    "approved_template": None,
    "clarification_questions": None,
    "user_answers": None,
    "needs_clarification": False,
    "clarification_attempted": False,
    "checkpoint_pending": False,
    "checkpoint_action": None,
    "user_feedback": None,
    "alternatives": None,
    "save_to_knowledge_base": False,
}

try:
    final_state = pipeline.invoke(initial_state)

    print(f"\n{'='*60}")
    if final_state["status"] == "done":
        print(f"  ✓ УСПЕХ за {final_state['iterations']} итераций")
        print(f"  Код: {session_dir}/final.lua")

        # Показываем код
        final_code = (session_dir / "final.lua").read_text(encoding="utf-8")
        print(f"\n{'='*60}")
        print("Сгенерированный код:")
        print(f"{'='*60}")
        print(final_code)
        print(f"{'='*60}")
    else:
        print(f"  ✗ ОШИБКА после {final_state['iterations']} итераций")
        if final_state.get("errors"):
            print(f"  Ошибки: {final_state['errors'][:200]}")
    print(f"{'='*60}\n")

except Exception as e:
    print(f"\n✗ Ошибка: {e}\n")
    import traceback
    traceback.print_exc()
