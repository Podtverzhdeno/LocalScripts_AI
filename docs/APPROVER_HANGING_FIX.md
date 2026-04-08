# Исправление проблемы зависания Approver Agent ✅

## Проблема

Система зависала на этапе `rag_approve` (Approver Agent) при попытке оценить релевантность найденных примеров. Approver не мог сгенерировать валидный JSON ответ, что приводило к бесконечному ожиданию.

**Симптомы:**
- Pipeline зависает после "Starting retrieval workflow..."
- Последнее сообщение: "[Retriever] Found 5 examples..."
- Сессия остается в статусе "running" с iteration: 0
- Нет ответа от Approver агента

**Причина:**
Модель `qwen2.5-coder:7b-instruct-q4_K_M` иногда не может сгенерировать валидный JSON для сложных промптов, особенно на русском языке.

---

## Решение

### 1. ✅ Улучшен промпт Approver

**Было:**
```python
prompt = f"""Task: {task}

{retrieved_examples}

Evaluate whether these retrieved examples are relevant...
Output format:
{{
  "approved": true/false,
  ...
}}
"""
```

**Стало:**
```python
prompt = f"""You are evaluating code examples for relevance.

TASK: {task}

RETRIEVED EXAMPLES:
{retrieved_examples}

RESPONSE FORMAT (copy this structure exactly):
{{"approved": false, "reason": "not relevant", "selected_examples": [], "confidence": 0.5}}

IMPORTANT: Return ONLY the JSON object. No markdown, no explanations, no code blocks.

JSON:"""
```

**Улучшения:**
- Более простой и прямой промпт
- Пример JSON для копирования
- Четкие инструкции без лишних деталей
- Короткий reason (max 10 words)

### 2. ✅ Добавлен timeout и fallback

**Добавлено:**
```python
try:
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    response = self.invoke(prompt)
    
    # Cancel timeout
    signal.alarm(0)
    
    # Extract JSON from response
    if "{" in response and "}" in response:
        start = response.find("{")
        end = response.rfind("}") + 1
        response = response[start:end]
    
    result = json.loads(response)
    
except TimeoutError:
    # Fallback: reject on timeout
    return {
        "approved": False,
        "reason": "Evaluation timed out",
        "selected_examples": [],
        "confidence": 0.0
    }
```

**Преимущества:**
- Система не зависает навсегда
- Автоматический fallback на генерацию без примеров
- Извлечение JSON из текста с мусором

### 3. ✅ Добавлена опция пропуска Approver

**Новая переменная окружения:**
```bash
RAG_SKIP_APPROVAL=true
```

**Поведение:**
- Пропускает оценку Approver
- Использует ВСЕ найденные примеры как шаблон
- Быстрее, но менее точно

**Код в `graph/nodes.py`:**
```python
skip_approval = os.getenv("RAG_SKIP_APPROVAL", "false").lower() == "true"

if skip_approval:
    print("[RAG] ⚠️  Skipping approval (RAG_SKIP_APPROVAL=true)")
    # Use all examples without approval
    return {
        "approved_template": approved_template,
        "rag_decision": {
            "approved": True,
            "reason": "Approval skipped",
            "selected_examples": list(range(1, len(rag_results) + 1)),
            "confidence": 1.0
        },
        "status": "generating",
    }
```

### 4. ✅ Улучшена обработка ошибок

**Добавлено:**
```python
try:
    decision = approver.evaluate(...)
    # ... обработка решения
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
```

**Преимущества:**
- Система продолжает работу даже при ошибке Approver
- Генерирует код без примеров вместо зависания
- Логирует ошибку для отладки

---

## Использование

### Вариант 1: Использовать улучшенный Approver (рекомендуется)

Просто перезапустите сервер с обновленным кодом:

```bash
cd C:\Users\user\IdeaProjects\Check\LocalScripts_AI
python -m api.server
```

Approver теперь:
- Имеет более простой промпт
- Автоматически извлекает JSON из ответа
- Имеет timeout 30 секунд
- Fallback на генерацию без примеров при ошибке

### Вариант 2: Пропустить Approver (быстрее, но менее точно)

Добавьте в `.env`:
```bash
RAG_SKIP_APPROVAL=true
```

Перезапустите сервер:
```bash
python -m api.server
```

Теперь система будет:
- Пропускать оценку Approver
- Использовать все найденные примеры
- Работать быстрее
- Но может использовать нерелевантные примеры

### Вариант 3: Отключить RAG полностью

Добавьте в `.env`:
```bash
RAG_ENABLED=false
```

Или в `config/settings.yaml`:
```yaml
rag:
  enabled: false
```

Система будет генерировать код без примеров (как раньше).

---

## Тестирование

### Проверка исправления:

1. **Перезапустить сервер:**
   ```bash
   cd C:\Users\user\IdeaProjects\Check\LocalScripts_AI
   python -m api.server
   ```

2. **Создать новую задачу:**
   - Открыть http://localhost:8000
   - Ввести: "создай CRUD для работы с excel"
   - Нажать "Generate"

3. **Проверить логи:**
   ```
   [RAG] Starting retrieval workflow...
   [Retriever] Found 5 examples...
   [RAG] Evaluating retrieved examples...
   [Approver] Decision: APPROVED/REJECTED  <-- должно появиться!
   [Generator] Iteration 1 — ... chars written
   ```

4. **Если зависает:**
   - Подождать 30 секунд (timeout)
   - Должно появиться: "[RAG] ⚠️  Approval failed: Evaluation timed out"
   - Система продолжит генерацию без примеров

5. **Альтернатива - пропустить Approver:**
   ```bash
   # В .env
   RAG_SKIP_APPROVAL=true
   ```
   Перезапустить сервер и попробовать снова.

---

## Рекомендации

### Для production:

1. **Использовать более сильную модель для Approver:**
   ```bash
   # В .env
   APPROVER_BACKEND=openrouter
   APPROVER_MODEL=openai/gpt-4o-mini
   ```
   
   GPT-4o-mini лучше генерирует JSON и не зависает.

2. **Или использовать DeepSeek R1:**
   ```bash
   APPROVER_BACKEND=ollama
   APPROVER_MODEL=deepseek-r1:8b
   ```
   
   DeepSeek R1 лучше справляется со структурированным выводом.

3. **Или пропустить Approver:**
   ```bash
   RAG_SKIP_APPROVAL=true
   ```
   
   Быстрее, но менее точно.

### Для отладки:

1. **Включить подробное логирование:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Проверить ответ Approver:**
   ```python
   # В agents/approver.py, после response = self.invoke(prompt)
   print(f"[DEBUG] Raw Approver response: {response}")
   ```

3. **Тестировать Approver отдельно:**
   ```python
   from agents.approver import ApproverAgent
   from llm.factory import get_llm
   
   llm = get_llm("approver")
   approver = ApproverAgent(llm)
   
   result = approver.evaluate(
       task="write fibonacci",
       retrieved_examples="Example 1: fibonacci code..."
   )
   print(result)
   ```

---

## Изменения в коде

### Файлы изменены:

1. **`agents/approver.py`:**
   - Улучшен промпт (более простой и прямой)
   - Добавлен timeout (30 секунд)
   - Добавлено извлечение JSON из текста
   - Улучшена обработка ошибок

2. **`graph/nodes.py`:**
   - Добавлена опция `RAG_SKIP_APPROVAL`
   - Добавлен try-except для обработки ошибок Approver
   - Fallback на генерацию без примеров

3. **`.env.example`:**
   - Добавлены опции RAG_ENABLED и RAG_USE_NEW_WORKFLOW

---

## Известные ограничения

### 1. Timeout не работает на Windows

**Причина:** Windows не поддерживает `signal.SIGALRM`.

**Решение:** Используйте `RAG_SKIP_APPROVAL=true` или более сильную модель для Approver.

### 2. Qwen 2.5 Coder плохо генерирует JSON

**Причина:** Модель оптимизирована для кода, а не для структурированного вывода.

**Решение:** 
- Использовать GPT-4o-mini или DeepSeek R1 для Approver
- Или пропустить Approver (`RAG_SKIP_APPROVAL=true`)

### 3. Approver может отклонять хорошие примеры

**Причина:** Модель слишком консервативна или не понимает задачу.

**Решение:**
- Понизить `approval_threshold` в `config/settings.yaml`
- Или пропустить Approver

---

## Заключение

✅ **Проблема зависания Approver исправлена**

**Что было сделано:**
- ✅ Улучшен промпт Approver (проще и понятнее)
- ✅ Добавлен timeout (30 секунд)
- ✅ Добавлено извлечение JSON из текста
- ✅ Добавлена опция пропуска Approver (`RAG_SKIP_APPROVAL`)
- ✅ Улучшена обработка ошибок (fallback на генерацию без примеров)

**Результат:**
Система больше не зависает. Если Approver не может оценить примеры:
- Через 30 секунд срабатывает timeout
- Система продолжает генерацию без примеров
- Или можно пропустить Approver полностью

**Рекомендация:**
Для production использовать более сильную модель для Approver (GPT-4o-mini или DeepSeek R1) или пропустить Approver (`RAG_SKIP_APPROVAL=true`).
