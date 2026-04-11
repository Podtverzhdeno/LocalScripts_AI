"""
Автоматический тест для 8 задач LowCode из публичной выборки MTS Octapi.
Проверяет, что модель qwen2.5-coder:7b с RAG примерами корректно решает задачи.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Установить LowCode режим
os.environ["USE_LOWCODE_PROMPTS"] = "true"
os.environ["RAG_ENABLED"] = "true"

# Добавить путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from graph.pipeline import run_pipeline
from config.loader import load_settings


# ============================================================
# Тестовые задачи из PDF
# ============================================================

LOWCODE_TASKS = [
    {
        "name": "1. Последний элемент массива",
        "task": "Из полученного списка email получи последний.",
        "expected_patterns": [
            r"wf\.vars\.emails",
            r"#wf\.vars\.emails"
        ],
        "expected_code": "return wf.vars.emails[#wf.vars.emails]",
        "context": {
            "wf": {
                "vars": {
                    "emails": ["user1@example.com", "user2@example.com", "user3@example.com"]
                }
            }
        }
    },
    {
        "name": "2. Счётчик попыток",
        "task": "Увеличивай значение переменной try_count_n на каждой итерации",
        "expected_patterns": [
            r"wf\.vars\.try_count_n",
            r"\+\s*1"
        ],
        "expected_code": "return wf.vars.try_count_n + 1",
        "context": {
            "wf": {
                "vars": {
                    "try_count_n": 3
                }
            }
        }
    },
    {
        "name": "3. Очистка значений в переменных",
        "task": "Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL",
        "expected_patterns": [
            r"wf\.vars\.RESTbody",
            r"pairs\(",
            r"nil"
        ],
        "context": {
            "wf": {
                "vars": {
                    "RESTbody": {
                        "result": [
                            {"ID": 123, "ENTITY_ID": 456, "CALL": "example", "OTHER": "value"}
                        ]
                    }
                }
            }
        }
    },
    {
        "name": "4. Приведение времени к ISO 8601",
        "task": "Преобразуй время из формата 'YYYYMMDD' и 'HHMMSS' в строку в формате ISO 8601",
        "expected_patterns": [
            r"wf\.vars\.json\.IDOC\.ZCDF_HEAD\.DATUM",
            r"wf\.vars\.json\.IDOC\.ZCDF_HEAD\.TIME",
            r"string\.format"
        ],
        "context": {
            "wf": {
                "vars": {
                    "json": {
                        "IDOC": {
                            "ZCDF_HEAD": {
                                "DATUM": "20231015",
                                "TIME": "153000"
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "name": "5. Проверка типа данных",
        "task": "Как преобразовать структуру данных так, чтобы все элементы items в ZCDF_PACKAGES всегда были представлены в виде массивов",
        "expected_patterns": [
            r"function\s+ensureArray",
            r"type\(",
            r"ipairs"
        ],
        "context": {
            "wf": {
                "vars": {
                    "json": {
                        "IDOC": {
                            "ZCDF_HEAD": {
                                "ZCDF_PACKAGES": [
                                    {"items": [{"sku": "A"}, {"sku": "B"}]},
                                    {"items": {"sku": "C"}}
                                ]
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "name": "6. Фильтрация элементов массива",
        "task": "Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown",
        "expected_patterns": [
            r"_utils\.array\.new\(\)",
            r"wf\.vars\.parsedCsv",
            r"ipairs",
            r"Discount",
            r"Markdown"
        ],
        "context": {
            "wf": {
                "vars": {
                    "parsedCsv": [
                        {"SKU": "A001", "Discount": "10%", "Markdown": ""},
                        {"SKU": "A002", "Discount": "", "Markdown": "5%"}
                    ]
                }
            }
        }
    },
    {
        "name": "7. Дополнение существующего кода",
        "task": "Добавь переменную с квадратом числа",
        "expected_patterns": [
            r"tonumber",
            r"\*\s*n"
        ],
        "context": {}
    },
    {
        "name": "8. Конвертация времени",
        "task": "Конвертируй время в переменной recallTime в unix-формат",
        "expected_patterns": [
            r"wf\.initVariables\.recallTime",
            r"function.*parse.*epoch",
            r"1970"
        ],
        "context": {
            "wf": {
                "initVariables": {
                    "recallTime": "2023-10-15T15:30:00+00:00"
                }
            }
        }
    }
]


# ============================================================
# Функции тестирования
# ============================================================

def test_task(task_data, verbose=True):
    """
    Тестирует одну задачу.

    Returns:
        (success: bool, message: str, code: str)
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Тест: {task_data['name']}")
        print(f"Задача: {task_data['task']}")
        print(f"{'='*60}")

    try:
        # Создать временную директорию для сессии
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = Path(__file__).parent / "workspace" / f"test_session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Запуск pipeline
        result = run_pipeline(
            task=task_data["task"],
            session_dir=str(session_dir),
            max_iterations=3
        )

        if result["status"] != "success":
            return False, f"Pipeline failed: {result.get('error', 'Unknown error')}", ""

        code = result.get("final_code", "")

        if not code:
            return False, "No code generated", ""

        # Проверка паттернов
        missing_patterns = []
        for pattern in task_data["expected_patterns"]:
            if not re.search(pattern, code, re.IGNORECASE):
                missing_patterns.append(pattern)

        if missing_patterns:
            return False, f"Missing patterns: {', '.join(missing_patterns)}", code

        if verbose:
            print(f"\n[OK] Код сгенерирован успешно")
            print(f"Длина: {len(code)} символов")
            print(f"Итераций: {result.get('iterations', 0)}")

        return True, "OK", code

    except Exception as e:
        return False, f"Exception: {str(e)}", ""


def run_all_tests(verbose=True):
    """
    Запускает все тесты и выводит статистику.
    """
    print("\n" + "="*60)
    print("  LocalScript LowCode Test Suite")
    print("  Модель: qwen2.5-coder:7b-instruct-q4_K_M")
    print("  Режим: USE_LOWCODE_PROMPTS=true, RAG_ENABLED=true")
    print("="*60)

    results = []
    passed = 0
    failed = 0

    for i, task in enumerate(LOWCODE_TASKS, 1):
        success, message, code = test_task(task, verbose=verbose)

        results.append({
            "name": task["name"],
            "success": success,
            "message": message,
            "code": code
        })

        if success:
            passed += 1
            print(f"\n[PASS] {task['name']}")
        else:
            failed += 1
            print(f"\n[FAIL] {task['name']}")
            print(f"  Причина: {message}")
            if code and verbose:
                print(f"  Сгенерированный код (первые 200 символов):")
                print(f"  {code[:200]}...")

    # Итоговая статистика
    print("\n" + "="*60)
    print("  РЕЗУЛЬТАТЫ")
    print("="*60)
    print(f"Пройдено: {passed}/{len(LOWCODE_TASKS)} ({passed*100//len(LOWCODE_TASKS)}%)")
    print(f"Провалено: {failed}/{len(LOWCODE_TASKS)}")

    if passed >= 6:
        print("\n[SUCCESS] Цель достигнута: 6+ задач пройдено!")
    elif passed >= 4:
        print("\n[WARNING] Частичный успех: 4-5 задач пройдено")
    else:
        print("\n[FAIL] Требуется улучшение: менее 4 задач пройдено")

    print("="*60)

    return results, passed, failed


# ============================================================
# Главная функция
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test LowCode tasks with LocalScript")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--task", "-t", type=int, help="Run specific task number (1-8)")

    args = parser.parse_args()

    if args.task:
        # Запуск одной задачи
        if 1 <= args.task <= len(LOWCODE_TASKS):
            task = LOWCODE_TASKS[args.task - 1]
            success, message, code = test_task(task, verbose=True)

            print(f"\n{'='*60}")
            if success:
                print(f"[PASS] Задача {args.task} ПРОЙДЕНА")
            else:
                print(f"[FAIL] Задача {args.task} ПРОВАЛЕНА: {message}")
            print(f"{'='*60}")

            if code:
                print(f"\nСгенерированный код:\n")
                print(code)

            sys.exit(0 if success else 1)
        else:
            print(f"Ошибка: номер задачи должен быть от 1 до {len(LOWCODE_TASKS)}")
            sys.exit(1)
    else:
        # Запуск всех тестов
        results, passed, failed = run_all_tests(verbose=args.verbose)
        sys.exit(0 if failed == 0 else 1)
