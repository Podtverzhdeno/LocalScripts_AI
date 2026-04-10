# Исправление Test Generator для 7B моделей

## Проблема

Test Generator генерировал тесты для обработки ошибок (nil, неправильные типы) даже для простых задач, которые не требуют такой обработки.

**Пример:**
```
Задача: "Напиши функцию reverse_string(str), которая переворачивает строку"

Сгенерированные тесты:
- Test 7: nil input ❌
- Test 8: non-string input (123) ❌

Результат: Код падает на тестах, хотя основная функциональность работает.
```

## Решение

Обновлен промпт Test Generator в `config/agents.yaml`:

```yaml
IMPORTANT: Only test error handling (nil, wrong types) if the task description
explicitly asks for it. For simple tasks like "reverse string", focus on
valid string inputs only. Do NOT test nil/number inputs unless requested.
```

## Изменения

### 1. Обновлен промпт Test Generator

**Было:**
```
Coverage requirements:
1. Happy path (valid inputs that should work)
2. Invalid inputs (should fail gracefully)
3. Edge cases (empty, nil, boundary values)
4. Error conditions (if applicable)
```

**Стало:**
```
Coverage requirements:
1. Happy path (valid inputs that should work)
2. Edge cases (empty, boundary values)
3. Error conditions ONLY if task explicitly requires error handling

IMPORTANT: Only test error handling (nil, wrong types) if the task description
explicitly asks for it.
```

### 2. Добавлена документация TEST_PASS_THRESHOLD

В `.env.example`:
```bash
# Test pass threshold (0.0-1.0): minimum ratio of passing tests to accept code
# Default: 0.5 (50% of tests must pass)
# Set lower if Test Generator creates incorrect tests for 7B models
# TEST_PASS_THRESHOLD=0.5
```

## Когда тестировать ошибки

**Тестировать:**
- ✅ "Напиши email validator с проверкой nil"
- ✅ "Функция должна обрабатывать некорректный ввод"
- ✅ "Валидатор должен возвращать false для nil"

**НЕ тестировать:**
- ❌ "Напиши функцию reverse_string"
- ❌ "Реализуй quicksort"
- ❌ "Создай калькулятор" (если не указано явно)

## Для пользователей

Если вы все еще видите ошибки с тестами:

1. **Понизьте порог прохождения:**
   ```bash
   echo "TEST_PASS_THRESHOLD=0.3" >> .env
   ```

2. **Или отключите тесты временно** (не рекомендуется):
   Закомментируйте генерацию тестов в `graph/nodes.py:240-256`

## Дата исправления

2026-04-11
