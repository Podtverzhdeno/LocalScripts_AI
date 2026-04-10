"""
Fast test without RAG - tests all 8 public tasks.
"""

import sys
import time
import tempfile
from pathlib import Path

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from graph.pipeline import run_pipeline
from llm.factory import get_llm

# Public tasks from PDF
PUBLIC_TASKS = [
    {
        "id": 1,
        "name": "Последний элемент массива",
        "task": "Из полученного списка email получи последний",
        "context": '{"wf": {"vars": {"emails": ["user1@example.com", "user2@example.com", "user3@example.com"]}}}',
        "expected_pattern": "wf.vars.emails[#wf.vars.emails]",
        "difficulty": 1
    },
    {
        "id": 2,
        "name": "Счетчик попыток",
        "task": "Увеличивай значение переменной try_count_n на каждой итерации",
        "context": '{"wf": {"vars": {"try_count_n": 3}}}',
        "expected_pattern": "wf.vars.try_count_n + 1",
        "difficulty": 1
    },
    {
        "id": 3,
        "name": "Очистка значений",
        "task": "Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL",
        "context": '{"wf": {"vars": {"RESTbody": {"result": [{"ID": 123, "ENTITY_ID": 456, "CALL": "example", "OTHER": "value"}]}}}}',
        "expected_pattern": "nil",
        "difficulty": 2
    },
    {
        "id": 4,
        "name": "Фильтрация массива",
        "task": "Из полученного массива users оставь только тех, у кого поле active равно true",
        "context": '{"wf": {"vars": {"users": [{"name": "Alice", "active": true}, {"name": "Bob", "active": false}, {"name": "Charlie", "active": true}]}}}',
        "expected_pattern": "active == true",
        "difficulty": 2
    },
    {
        "id": 5,
        "name": "Конкатенация строк",
        "task": "Объедини имя и фамилию пользователя в одну строку через пробел",
        "context": '{"wf": {"vars": {"first_name": "Иван", "last_name": "Петров"}}}',
        "expected_pattern": ".. \" \" ..",
        "difficulty": 1
    },
    {
        "id": 6,
        "name": "Проверка email",
        "task": "Проверь, является ли строка валидным email адресом",
        "context": '{"wf": {"vars": {"email": "test@example.com"}}}',
        "expected_pattern": "@",
        "difficulty": 2
    },
    {
        "id": 7,
        "name": "Сумма элементов",
        "task": "Посчитай сумму всех чисел в массиве numbers",
        "context": '{"wf": {"vars": {"numbers": [10, 20, 30, 40, 50]}}}',
        "expected_pattern": "for",
        "difficulty": 2
    },
    {
        "id": 8,
        "name": "Форматирование даты",
        "task": "Преобразуй timestamp в читаемый формат даты DD.MM.YYYY",
        "context": '{"wf": {"vars": {"timestamp": 1609459200}}}',
        "expected_pattern": "os.date",
        "difficulty": 3
    }
]


def main():
    print("=" * 60)
    print("LocalScript Public Task Dataset Test (Fast - No RAG)")
    print("=" * 60)
    print(f"Total tasks: {len(PUBLIC_TASKS)}")

    # Get LLM without RAG
    llm = get_llm()
    print(f"Model: {llm.model}")
    print("=" * 60)
    print()

    results = []
    total_time = 0

    # Create temp session directory
    session_dir = tempfile.mkdtemp(prefix="localscript_test_")
    print(f"Session dir: {session_dir}\n")

    for task_data in PUBLIC_TASKS:
        print("=" * 60)
        print(f"Task #{task_data['id']}: {task_data['name']}")
        print("=" * 60)
        print(f"Description: {task_data['task']}")
        print(f"Difficulty: {'⭐' * task_data['difficulty']}")
        print()

        start_time = time.time()

        try:
            # Run pipeline WITHOUT RAG (rag_system=None)
            result = run_pipeline(
                task=task_data['task'],
                session_dir=session_dir,
                llm=llm,
                rag_system=None,  # Disable RAG for speed
                max_iterations=5
            )

            elapsed = time.time() - start_time
            total_time += elapsed

            success = result.get("success", False)
            code = result.get("code", "")
            iterations = result.get("iterations", 0)

            # Check if expected pattern is in code
            pattern_found = task_data["expected_pattern"].lower() in code.lower()

            results.append({
                "id": task_data["id"],
                "name": task_data["name"],
                "success": success,
                "pattern_found": pattern_found,
                "time": elapsed,
                "iterations": iterations,
                "code_length": len(code)
            })

            status = "✓ PASS" if success and pattern_found else "✗ FAIL"
            print(f"\n{status}")
            print(f"Time: {elapsed:.1f}s | Iterations: {iterations} | Pattern: {'✓' if pattern_found else '✗'}")
            print(f"Code length: {len(code)} chars")

            if code:
                print("\nGenerated code:")
                print("-" * 60)
                print(code[:300] + ("..." if len(code) > 300 else ""))
                print("-" * 60)

        except Exception as e:
            elapsed = time.time() - start_time
            total_time += elapsed

            results.append({
                "id": task_data["id"],
                "name": task_data["name"],
                "success": False,
                "pattern_found": False,
                "time": elapsed,
                "iterations": 0,
                "code_length": 0
            })

            print(f"\n✗ ERROR: {str(e)[:200]}")
            print(f"Time: {elapsed:.1f}s")

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = sum(1 for r in results if r["success"])
    pattern_matches = sum(1 for r in results if r["pattern_found"])
    avg_time = total_time / len(results)
    avg_iterations = sum(r["iterations"] for r in results) / len(results)

    print(f"Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    print(f"Pattern matches: {pattern_matches}/{len(results)} ({pattern_matches/len(results)*100:.1f}%)")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per task: {avg_time:.1f}s")
    print(f"Average iterations: {avg_iterations:.1f}")
    print()

    # Detailed results
    print("Detailed results:")
    print("-" * 60)
    for r in results:
        status = "✓" if r["success"] and r["pattern_found"] else "✗"
        print(f"{status} Task #{r['id']:2d}: {r['name']:30s} | {r['time']:5.1f}s | {r['iterations']} iter")

    print("=" * 60)


if __name__ == "__main__":
    main()
