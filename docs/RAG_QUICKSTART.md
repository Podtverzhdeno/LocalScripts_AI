# RAG Workflow: Retriever + Approver Agents

## Быстрый старт

### 1. Установка зависимостей

Все необходимые зависимости уже в `requirements.txt`:
- `langchain-core`
- `langchain-chroma`
- `langchain-community`

### 2. Инициализация RAG базы

```bash
python -m rag.cli init
```

### 3. Запуск примера

```bash
# Базовый workflow
python examples/rag_workflow_example.py --mode workflow

# Сравнение старого и нового подходов
python examples/rag_workflow_example.py --mode comparison
```

### 4. Запуск тестов

```bash
pytest tests/test_rag_agents.py -v
```

## Архитектура

```
┌─────────────┐
│  User Task  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Retriever Agent │ ──→ Поиск в ChromaDB
└────────┬────────┘     (топ-5 примеров)
         │
         ▼
┌─────────────────┐
│ Approver Agent  │ ──→ Оценка релевантности
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
APPROVED   REJECTED
    │         │
    ▼         ▼
┌─────────────────┐
│ Generator Agent │ ──→ Код с шаблоном или с нуля
└────────┬────────┘
         │
         ▼
    [Validator]
         │
         ▼
    [Reviewer]
         │
         ▼
     SUCCESS
```

## Использование

### Программное API

```python
from rag.system import create_rag_system
from agents.retriever import RetrieverAgent
from agents.approver import ApproverAgent
from agents.generator import GeneratorAgent
from llm.factory import get_llm

# Инициализация
rag_system = create_rag_system()
llm = get_llm()

retriever = RetrieverAgent(llm, rag_system=rag_system)
approver = ApproverAgent(llm)
generator = GeneratorAgent(llm, rag_system=rag_system)

# Workflow
task = "write fibonacci with memoization"

# 1. Поиск
results = retriever.search(task=task, k=5)

# 2. Форматирование
formatted = retriever.format_examples_for_approval(results)

# 3. Одобрение
decision = approver.evaluate(
    task=task,
    retrieved_examples=formatted
)

# 4. Генерация
if decision['approved']:
    approved_docs = approver.extract_approved_examples(
        results,
        decision['selected_examples']
    )
    template = rag_system.format_context([doc for doc, _ in approved_docs])
    code = generator.generate(task=task, approved_template=template)
else:
    code = generator.generate(task=task)

print(f"Decision: {decision['approved']}")
print(f"Reason: {decision['reason']}")
print(f"Code: {len(code)} chars")
```

### Интеграция в pipeline

В `graph/nodes.py` уже добавлены новые ноды:

```python
from graph.nodes import make_nodes

# Создание нод с RAG workflow
node_generate, node_validate, node_review, node_fail, node_rag_retrieve, node_rag_approve = make_nodes(
    llm=llm,
    rag_system=rag_system,
    use_rag_workflow=True  # Включить новый workflow
)
```

## Конфигурация

### Для маленьких моделей (7B-11B)

```yaml
# config/settings.yaml
agents:
  retriever:
    backend: ollama
    model: qwen2.5-coder:7b  # Быстрая локальная модель
  
  approver:
    backend: openrouter
    model: openai/gpt-4o-mini  # Более сильная модель для оценки
  
  generator:
    backend: ollama
    model: qwen2.5-coder:7b

rag:
  enabled: true
  workflow_mode: "approve"  # Использовать Retriever+Approver
  approval_threshold: 0.7   # Консервативный порог (выше = строже)
  max_examples: 3           # Меньше примеров для маленьких моделей
```

### Для больших моделей (30B+)

```yaml
agents:
  retriever:
    backend: ollama
    model: qwen2.5-coder:32b
  
  approver:
    backend: ollama
    model: qwen2.5-coder:32b  # Можно использовать локальную модель
  
  generator:
    backend: ollama
    model: qwen2.5-coder:32b

rag:
  approval_threshold: 0.5  # Более мягкий порог
  max_examples: 5          # Больше контекста
```

## Примеры вывода

### ✓ Одобрено

```
[RAG] Starting retrieval workflow...
[Retriever] Searching for: 'write fibonacci with memoization'
[Retriever] Found 5 examples:
[Retriever]   [1] algorithm    (score: 0.892) - Fibonacci with memoization...
[Retriever]   [2] algorithm    (score: 0.745) - Dynamic programming...
[Retriever]   [3] best-practice (score: 0.623) - Use local variables...

[RAG] Evaluating retrieved examples...
[Approver] Decision: APPROVED
[Approver] Reason: Example 1 directly demonstrates fibonacci with memoization, which is exactly what the task requires
[Approver] Confidence: 0.95
[Approver] Selected examples: [1]

[RAG] ✓ APPROVED - Using 1 example(s) as template
[Generator] Using approved RAG template
[Generator] Iteration 1 — 342 chars written
[Validator] ✓ Code OK
[Reviewer] ✓ Approved

✓ SUCCESS in 1 iteration(s)
```

### ✗ Отклонено

```
[RAG] Starting retrieval workflow...
[Retriever] Searching for: 'validate email addresses'
[Retriever] Found 5 examples:
[Retriever]   [1] string       (score: 0.612) - Advanced pattern matching...
[Retriever]   [2] integration  (score: 0.589) - Email validation with RFC 5322...

[RAG] Evaluating retrieved examples...
[Approver] Decision: REJECTED
[Approver] Reason: While example 2 shows email validation, it's for a different context. The task needs a simpler standalone validator.
[Approver] Confidence: 0.72

[RAG] ✗ REJECTED - The task needs a simpler standalone validator
[RAG] Generating from scratch
[Generator] Iteration 1 — 287 chars written
[Validator] ✓ Code OK
[Reviewer] ✓ Approved

✓ SUCCESS in 1 iteration(s)
```

## Преимущества

### Для маленьких моделей (7B-11B)
- ✅ Выше успешность генерации
- ✅ Чище промпты (либо качественный шаблон, либо ничего)
- ✅ Меньше retry из-за плохих примеров
- ✅ Консервативное одобрение предотвращает путаницу

### Для всех моделей
- 📊 Прозрачность решений
- 🔍 Легко отлаживать
- ⚙️ Гибкая настройка под размер модели
- 📈 Метрики approval rate и confidence

## Метрики

### Отслеживание эффективности

```python
# Логирование решений
approval_rate = approved_count / total_tasks
avg_confidence = sum(confidences) / len(confidences)

print(f"Approval rate: {approval_rate:.2%}")
print(f"Average confidence: {avg_confidence:.2f}")
```

### Анализ логов

```bash
# Количество одобрений
grep -c "APPROVED" workspace/*/report.md

# Количество отклонений
grep -c "REJECTED" workspace/*/report.md

# Средняя уверенность
grep "Confidence:" workspace/*/report.md | awk '{sum+=$2; count++} END {print sum/count}'
```

## Troubleshooting

### Слишком много отклонений (< 30% approval rate)

1. Понизить `approval_threshold` в конфиге
2. Расширить базу знаний (добавить больше примеров)
3. Использовать более сильную модель для approver
4. Проверить, что retriever находит релевантные примеры

### Слишком много одобрений (> 80% approval rate), но низкое качество

1. Повысить `approval_threshold`
2. Использовать более сильную модель для approver
3. Уточнить промпт approver для более строгой оценки
4. Добавить дополнительные критерии оценки

### Медленная работа

1. Использовать более быструю модель для retriever (7B локально)
2. Уменьшить `max_examples` (меньше примеров для оценки)
3. Кэшировать решения для похожих задач
4. Запускать retriever и approver параллельно (будущая оптимизация)

## Структура файлов

```
LocalScripts_AI/
├── agents/
│   ├── retriever.py          # NEW: RetrieverAgent
│   ├── approver.py           # NEW: ApproverAgent
│   ├── generator.py          # UPDATED: поддержка approved_template
│   └── __init__.py           # UPDATED: экспорт новых агентов
├── graph/
│   └── nodes.py              # UPDATED: node_rag_retrieve, node_rag_approve
├── config/
│   └── agents.yaml           # UPDATED: промпты для retriever, approver
├── docs/
│   └── rag_workflow.md       # NEW: полная документация
├── examples/
│   └── rag_workflow_example.py  # NEW: примеры использования
├── tests/
│   └── test_rag_agents.py    # NEW: тесты для новых агентов
└── RAG_WORKFLOW_SUMMARY.md   # NEW: краткое резюме
```

## Следующие шаги

1. ✅ Создать RetrieverAgent и ApproverAgent
2. ✅ Обновить GeneratorAgent для работы с шаблонами
3. ✅ Добавить новые ноды в pipeline
4. ✅ Написать документацию и примеры
5. ✅ Создать тесты
6. ⏳ Интегрировать в main.py (добавить CLI флаги)
7. ⏳ Добавить метрики и логирование
8. ⏳ Настроить оптимальные пороги для разных моделей
9. ⏳ Добавить кэширование решений

## Обратная связь

Если у вас есть вопросы или предложения по улучшению RAG workflow, создайте issue в репозитории.

## Лицензия

MIT
