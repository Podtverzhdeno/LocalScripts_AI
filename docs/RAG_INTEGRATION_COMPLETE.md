# RAG Workflow Integration - Complete ✅

## Статус: ЗАВЕРШЕНО

Интеграция RAG workflow с агентами Retriever и Approver успешно завершена и протестирована.

---

## Что было сделано

### 1. ✅ Добавлены поля в AgentState (`graph/state.py`)

Добавлены 4 новых поля для поддержки RAG workflow:

```python
# RAG workflow (NEW - for Retriever + Approver agents)
rag_results: Optional[list]        # Retrieved documents with scores from RetrieverAgent
rag_formatted: Optional[str]       # Formatted examples for ApproverAgent evaluation
rag_decision: Optional[dict]       # ApproverAgent decision: {"approved": bool, "reason": str, ...}
approved_template: Optional[str]   # Approved RAG template for GeneratorAgent (if decision["approved"])
```

### 2. ✅ Интегрированы RAG ноды в граф (`graph/pipeline.py`)

**Обновлена функция `build_pipeline()`:**
- Принимает все 6 нод от `make_nodes()` (включая `node_rag_retrieve` и `node_rag_approve`)
- Добавлены параметры `llm_retriever`, `llm_approver`, `use_rag_workflow`
- Условное добавление RAG нод в граф:
  - Если `use_rag_workflow=True` и `rag_system` доступен → полный RAG workflow
  - Иначе → прямой переход к генерации (legacy режим)

**Граф с RAG workflow:**
```
START → rag_retrieve → rag_approve → generate → validate → review → END
```

**Граф без RAG (legacy):**
```
START → generate → validate → review → END
```

### 3. ✅ Обновлена функция `run_pipeline()`

- Добавлен параметр `use_rag_workflow: bool = True` (включен по умолчанию)
- Загрузка LLM для новых агентов: `llm_retriever`, `llm_approver`
- Передача всех параметров в `build_pipeline()`
- Инициализация RAG полей в `initial_state`
- Улучшенное логирование: показывает, какой workflow используется (NEW/LEGACY)

### 4. ✅ Обновлена конфигурация (`config/settings.yaml`)

**Добавлены настройки для новых агентов:**
```yaml
agents:
  retriever:
    # backend: ollama
    # model: qwen2.5-coder:7b    # Fast local RAG search
  approver:
    # backend: openrouter
    # model: openai/gpt-4o-mini  # Stronger model for relevance evaluation
```

**Обновлены настройки RAG:**
```yaml
rag:
  enabled: true
  use_new_workflow: true                 # NEW: Enable Retriever+Approver workflow
  retrieval_k: 5                         # Increased from 3 for better selection
  max_context_length: 2000               # Increased from 1500 for richer templates
  approval_threshold: 0.6                # NEW: Minimum confidence for approval
```

### 5. ✅ Создан интеграционный тест (`tests/test_rag_workflow_integration.py`)

**6 тестов покрывают все сценарии:**

1. `test_rag_workflow_enabled_in_graph` - проверяет, что RAG ноды добавлены в граф
2. `test_rag_workflow_disabled_in_graph` - проверяет, что RAG ноды НЕ добавлены при отключении
3. `test_full_workflow_with_approval` - полный цикл с одобрением примеров
4. `test_full_workflow_with_rejection` - полный цикл с отклонением примеров
5. `test_workflow_without_rag_system` - fallback на прямую генерацию
6. `test_state_fields_initialized` - проверка инициализации полей state

**Все тесты проходят:** ✅ 6/6 passed

---

## Архитектура

### Новый RAG Workflow (use_rag_workflow=True)

```
┌─────────────────────────────────────────────────────────────┐
│                     USER TASK                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  RETRIEVER AGENT (7B model)                                  │
│  - Searches ChromaDB for top-5 examples                      │
│  - Returns documents with similarity scores                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  APPROVER AGENT (stronger model, e.g. gpt-4o-mini)          │
│  - Evaluates relevance of retrieved examples                │
│  - Decision: APPROVE or REJECT                               │
│  - Confidence score: 0.0-1.0                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    ↓               ↓
            ┌──────────────┐  ┌──────────────┐
            │  APPROVED    │  │  REJECTED    │
            └──────────────┘  └──────────────┘
                    ↓               ↓
┌─────────────────────────────────────────────────────────────┐
│  GENERATOR AGENT (7B model)                                  │
│  - If APPROVED: uses examples as template                    │
│  - If REJECTED: generates from scratch                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  VALIDATOR AGENT (7B model)                                  │
│  - Compiles with luac                                        │
│  - Executes with lua                                         │
│  - Generates functional tests                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  REVIEWER AGENT (stronger model)                             │
│  - Code quality review                                       │
│  - Performance check                                         │
│  - Final approval                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
                      ✅ SUCCESS
```

### Преимущества для маленьких моделей (7B-12B)

1. **Точечная специализация**: Каждый агент решает одну задачу
   - Retriever: только поиск (быстро, локально)
   - Approver: только оценка релевантности (требует рассуждений → сильная модель)
   - Generator: только генерация кода (локально, с качественным шаблоном)

2. **Консервативное одобрение**: Плохой шаблон хуже, чем его отсутствие
   - Approver отклоняет сомнительные примеры
   - Generator получает либо качественный шаблон, либо ничего

3. **Гибридная конфигурация**: Оптимальное распределение нагрузки
   - Простые задачи (поиск, генерация) → локальные 7B модели
   - Сложные задачи (оценка, ревью) → облачные модели

4. **Прозрачность**: Видно, почему примеры одобрены/отклонены
   - Логирование решений Approver
   - Метрики: approval rate, confidence scores

---

## Использование

### Базовое (RAG workflow включен по умолчанию)

```bash
python main.py --task "write fibonacci with memoization"
```

Вывод:
```
[RAG] Initializing Knowledge Base...
[RAG] Status: ACTIVE
[RAG] Documents: 39
[RAG] Workflow: NEW (Retriever+Approver)

[RAG] Starting retrieval workflow...
[Retriever] Found 5 examples:
[Retriever]   [1] algorithm (score: 0.892) - Fibonacci with memoization...

[RAG] Evaluating retrieved examples...
[Approver] Decision: APPROVED
[Approver] Reason: Example 1 directly demonstrates fibonacci with memoization
[Approver] Confidence: 0.95
[RAG] ✓ APPROVED - Using 1 example(s) as template

[Generator] Iteration 1 — 342 chars written
[Validator] ✓ Code OK
[Reviewer] ✓ Approved
```

### Отключение RAG workflow (legacy режим)

```python
from graph.pipeline import run_pipeline

final_state = run_pipeline(
    task="write quicksort",
    session_dir="workspace/session_test",
    use_rag_workflow=False  # Отключить новый workflow
)
```

### Гибридная конфигурация для 7B моделей

В `.env`:
```bash
# Локальные модели для простых задач
GENERATOR_BACKEND=ollama
GENERATOR_MODEL=qwen2.5-coder:7b

RETRIEVER_BACKEND=ollama
RETRIEVER_MODEL=qwen2.5-coder:7b

VALIDATOR_BACKEND=ollama
VALIDATOR_MODEL=qwen2.5-coder:7b

# Облачные модели для сложных задач
APPROVER_BACKEND=openrouter
APPROVER_MODEL=openai/gpt-4o-mini

REVIEWER_BACKEND=openrouter
REVIEWER_MODEL=openai/gpt-4o-mini
```

---

## Тестирование

### Запуск интеграционных тестов

```bash
pytest tests/test_rag_workflow_integration.py -v
```

Результат:
```
test_rag_workflow_enabled_in_graph PASSED
test_rag_workflow_disabled_in_graph PASSED
test_full_workflow_with_approval PASSED
test_full_workflow_with_rejection PASSED
test_workflow_without_rag_system PASSED
test_state_fields_initialized PASSED

======================== 6 passed in 10.69s ========================
```

### Запуск всех тестов

```bash
pytest tests/ -v
```

---

## Метрики и мониторинг

### Логирование решений Approver

```python
[Approver] Decision: APPROVED/REJECTED
[Approver] Reason: <explanation>
[Approver] Confidence: 0.85
[Approver] Selected examples: [1, 3]
```

### Отслеживание approval rate

```python
# В будущем можно добавить метрики:
# - approval_rate = approved / total_retrievals
# - avg_confidence = sum(confidence) / total_decisions
# - template_usage_rate = approved_generations / total_generations
```

---

## Обратная совместимость

✅ **Полная обратная совместимость:**

1. Старый код работает без изменений
2. Legacy RAG режим доступен через `use_rag_workflow=False`
3. Если RAG отключен (`rag.enabled=false`), workflow автоматически переключается на прямую генерацию
4. Все существующие тесты проходят

---

## Следующие шаги (опционально)

### Улучшения для production:

1. **Метрики**: Добавить сбор статистики approval rate, confidence scores
2. **A/B тестирование**: Сравнить качество кода с/без RAG workflow
3. **Настройка порогов**: Подобрать оптимальный `approval_threshold` для разных размеров моделей
4. **Кэширование**: Кэшировать решения Approver для повторяющихся задач
5. **Feedback loop**: Использовать результаты Validator для улучшения Approver

### Оптимизации:

1. **Параллельный поиск**: Retriever может искать в нескольких коллекциях одновременно
2. **Batch approval**: Approver может оценивать несколько наборов примеров параллельно
3. **Adaptive k**: Динамически менять количество извлекаемых примеров на основе confidence

---

## Заключение

✅ **RAG workflow полностью интегрирован и готов к использованию**

Система оптимизирована для работы с маленькими моделями (7B-12B параметров) через:
- Точечную специализацию агентов
- Консервативное одобрение примеров
- Гибридную конфигурацию (локальные + облачные модели)
- Прозрачное логирование решений

Все тесты проходят, обратная совместимость сохранена.
