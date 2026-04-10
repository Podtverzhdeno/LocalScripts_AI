"""
Test LocalScript on public task dataset from MTS Octapi.
Tests all 8 tasks and measures success rate, time, iterations.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

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

# ============================================================
# Public tasks from PDF
# ============================================================

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
        "expected_pattern": "filteredEntry[key] = nil",
        "difficulty": 2
    },
    {
        "id": 4,
        "name": "ISO 8601 конвертация",
        "task": "Преобразуй время из формата 'YYYYMMDD' и 'HHMMSS' в строку в формате ISO 8601. Контекст: wf.vars.json.IDOC.ZCDF_HEAD.DATUM = '20231015', TIME = '153000'",
        "context": '{"wf": {"vars": {"json": {"IDOC": {"ZCDF_HEAD": {"DATUM": "20231015", "TIME": "153000"}}}}}}',
        "expected_pattern": "string.format",
        "difficulty": 3
    },
    {
        "id": 5,
        "name": "Проверка типа данных",
        "task": "Преобразуй структуру данных так, чтобы все элементы items в ZCDF_PACKAGES всегда были представлены в виде массивов. Контекст: wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES содержит объекты с полем items (может быть объектом или массивом)",
        "context": '{"wf": {"vars": {"json": {"IDOC": {"ZCDF_HEAD": {"ZCDF_PACKAGES": [{"items": [{"sku": "A"}]}, {"items": {"sku": "B"}}]}}}}}}',
        "expected_pattern": "ensureArray",
        "difficulty": 4
    },
    {
        "id": 6,
        "name": "Фильтрация массива",
        "task": "Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown. Контекст: wf.vars.parsedCsv = [{SKU='A001', Discount='10%', Markdown=''}, {SKU='A002', Discount='', Markdown='5%'}]",
        "context": '{"wf": {"vars": {"parsedCsv": [{"SKU": "A001", "Discount": "10%", "Markdown": ""}, {"SKU": "A002", "Discount": "", "Markdown": "5%"}]}}}',
        "expected_pattern": "_utils.array.new()",
        "difficulty": 2
    },
    {
        "id": 7,
        "name": "Дополнение кода",
        "task": "Добавь переменную с квадратом числа 5",
        "context": '{}',
        "expected_pattern": "n * n",
        "difficulty": 1
    },
    {
        "id": 8,
        "name": "Unix timestamp",
        "task": "Конвертируй время в переменной recallTime в unix-формат. Контекст: wf.initVariables.recallTime = '2023-10-15T15:30:00+00:00'",
        "context": '{"wf": {"initVariables": {"recallTime": "2023-10-15T15:30:00+00:00"}}}',
        "expected_pattern": "parse_iso8601",
        "difficulty": 5
    }
]

# ============================================================
# Test runner
# ============================================================

def run_test(task_data: dict, output_dir: Path) -> dict:
    """Run a single test task."""
    task_id = task_data["id"]
    task_name = task_data["name"]
    task_desc = task_data["task"]

    print(f"\n{'='*60}")
    print(f"Task #{task_id}: {task_name}")
    print(f"{'='*60}")
    print(f"Description: {task_desc}")
    print(f"Difficulty: {'⭐' * task_data['difficulty']}")

    # Create session directory
    session_dir = output_dir / f"task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save task info
    (session_dir / "task.txt").write_text(task_desc, encoding='utf-8')
    (session_dir / "context.json").write_text(task_data["context"], encoding='utf-8')

    # Run pipeline
    start_time = time.time()
    try:
        result = run_pipeline(
            task=task_desc,
            session_dir=str(session_dir),
            max_iterations=3,
            use_clarifier=False  # Disabled for speed
        )

        elapsed = time.time() - start_time

        # Check result
        success = result.get("status") == "success"
        final_code = result.get("final_code", "")
        iterations = result.get("iteration", 0)

        # Check if expected pattern is in code
        pattern_found = task_data["expected_pattern"].lower() in final_code.lower()

        print(f"\n{'─'*60}")
        print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Pattern found: {'✅' if pattern_found else '❌'} ({task_data['expected_pattern']})")
        print(f"Iterations: {iterations}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Code length: {len(final_code)} chars")

        return {
            "task_id": task_id,
            "name": task_name,
            "difficulty": task_data["difficulty"],
            "success": success,
            "pattern_found": pattern_found,
            "iterations": iterations,
            "time": elapsed,
            "code_length": len(final_code),
            "session_dir": str(session_dir)
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR: {e}")

        return {
            "task_id": task_id,
            "name": task_name,
            "difficulty": task_data["difficulty"],
            "success": False,
            "pattern_found": False,
            "iterations": 0,
            "time": elapsed,
            "code_length": 0,
            "error": str(e),
            "session_dir": str(session_dir)
        }


def main():
    """Run all tests and generate report."""
    print("="*60)
    print("LocalScript Public Task Dataset Test")
    print("="*60)
    print(f"Total tasks: {len(PUBLIC_TASKS)}")
    print(f"Model: qwen2.5-coder:7b-instruct-q4_K_M")
    print(f"Prompts: agents_lowcode.yaml")
    print("="*60)

    # Create output directory
    output_dir = Path("workspace") / f"public_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run all tests
    results = []
    for task_data in PUBLIC_TASKS:
        result = run_test(task_data, output_dir)
        results.append(result)
        time.sleep(2)  # Cooldown between tests

    # Generate report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    pattern_matches = sum(1 for r in results if r["pattern_found"])
    avg_time = sum(r["time"] for r in results) / total
    avg_iterations = sum(r["iterations"] for r in results) / total

    print(f"\nOverall:")
    print(f"  Success rate: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"  Pattern match: {pattern_matches}/{total} ({pattern_matches/total*100:.1f}%)")
    print(f"  Avg time: {avg_time:.1f}s")
    print(f"  Avg iterations: {avg_iterations:.1f}")

    print(f"\nBy difficulty:")
    for diff in range(1, 6):
        diff_results = [r for r in results if r["difficulty"] == diff]
        if diff_results:
            diff_success = sum(1 for r in diff_results if r["success"])
            print(f"  {'⭐'*diff}: {diff_success}/{len(diff_results)} ({diff_success/len(diff_results)*100:.0f}%)")

    print(f"\nDetailed results:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        pattern = "✅" if r["pattern_found"] else "❌"
        print(f"  {status} Task #{r['task_id']}: {r['name']}")
        print(f"     Pattern: {pattern} | Time: {r['time']:.1f}s | Iterations: {r['iterations']}")

    # Save report
    report_path = output_dir / "REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Public Task Dataset Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model:** qwen2.5-coder:7b-instruct-q4_K_M\n")
        f.write(f"**Prompts:** agents_lowcode.yaml\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Success rate: {successful}/{total} ({successful/total*100:.1f}%)\n")
        f.write(f"- Pattern match: {pattern_matches}/{total} ({pattern_matches/total*100:.1f}%)\n")
        f.write(f"- Avg time: {avg_time:.1f}s\n")
        f.write(f"- Avg iterations: {avg_iterations:.1f}\n\n")
        f.write(f"## Results\n\n")
        for r in results:
            f.write(f"### Task #{r['task_id']}: {r['name']}\n\n")
            f.write(f"- Status: {'✅ SUCCESS' if r['success'] else '❌ FAILED'}\n")
            f.write(f"- Pattern found: {'✅' if r['pattern_found'] else '❌'}\n")
            f.write(f"- Time: {r['time']:.1f}s\n")
            f.write(f"- Iterations: {r['iterations']}\n")
            f.write(f"- Session: `{r['session_dir']}`\n\n")

    print(f"\nReport saved to: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()
