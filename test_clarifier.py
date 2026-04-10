"""
Test ClarifierAgent with LowCode-specific tasks.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.clarifier import ClarifierAgent
from llm.factory import get_llm

# Test cases
TEST_CASES = [
    {
        "name": "Clear: last element",
        "task": "Из полученного списка email получи последний",
        "expected": "clear"
    },
    {
        "name": "Clear: increment counter",
        "task": "Увеличивай значение переменной try_count_n на каждой итерации",
        "expected": "clear"
    },
    {
        "name": "Clear: concatenate strings",
        "task": "Объедини имя и фамилию пользователя в одну строку через пробел",
        "expected": "clear"
    },
    {
        "name": "Ambiguous: process data",
        "task": "Обработай данные из REST запроса",
        "expected": "unclear"
    },
    {
        "name": "Ambiguous: clean values",
        "task": "Очисти значения переменных",
        "expected": "unclear"
    },
    {
        "name": "Ambiguous: format date",
        "task": "Преобразуй timestamp в дату",
        "expected": "unclear"
    }
]


def main():
    print("=" * 60)
    print("ClarifierAgent LowCode Test")
    print("=" * 60)
    print()

    llm = get_llm("clarifier")
    clarifier = ClarifierAgent(llm)

    results = []

    for test in TEST_CASES:
        print(f"Test: {test['name']}")
        print(f"Task: {test['task']}")
        print(f"Expected: {test['expected']}")

        questions = clarifier.analyze_task(test['task'])

        if questions is None:
            actual = "clear"
            print("Result: CLEAR (no questions)")
        else:
            actual = "unclear"
            print(f"Result: UNCLEAR ({len(questions)} questions)")
            for i, q in enumerate(questions, 1):
                print(f"  Q{i}: {q['question']}")
                print(f"      Options: {', '.join(q['options'])}")

        match = actual == test['expected']
        results.append(match)

        print(f"Status: {'✓ PASS' if match else '✗ FAIL'}")
        print("-" * 60)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
