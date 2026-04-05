<div align="center">

# ⚡ LocalScript

**Автономная агентская система для генерации и валидации Lua-кода**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-48%20passed-brightgreen.svg)](#-тестирование)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](#-mcp-сервер)

Опишите задачу на естественном языке — получите работающий, проверенный Lua-код.

**CLI** · **Web UI** · **REST API** · **MCP Server**

</div>

---

## Чем отличается от обычного чат-бота

LocalScript **реально запускает код**. Три AI-агента работают в цикле:

```
┌──────────┐     ┌───────────┐     ┌──────────┐
│ Generator│────▶│ Validator  │────▶│ Reviewer  │
│ пишет Lua│     │ luac + lua │     │ качество  │
└──────────┘     └───────────┘     └──────────┘
     ▲                │                  │
     │    ошибки      │     фидбек       │
     └────────────────┘                  │
     └───────────────────────────────────┘
```

- **Generator** — пишет Lua-код по описанию задачи (опционально с reasoning-стратегией)
- **Validator** — компилирует через `luac` и запускает через `lua` — реальные ошибки, не галлюцинации
- **Reviewer** — проверяет качество кода, одобряет или запрашивает доработки
- Цикл повторяется до `max_iterations` раз, каждая попытка сохраняется

Вдохновлён [ChatDev](https://github.com/OpenBMB/ChatDev), но с **реальным выполнением кода** вместо симулированного тестирования.

---

## 🚀 Быстрый старт

### 1. Установка

```bash
git clone https://github.com/Podtverzhdeno/LocalScripts_AI
cd LocalScripts_AI
pip install -r requirements.txt
```

### 2. Настройка

```bash
cp .env.example .env
# Отредактируйте .env — добавьте API-ключ (см. «LLM-бэкенды» ниже)
```

### 3. Запуск

```bash
python main.py --task "write a fibonacci function with memoization"
```

Вывод:
```
============================================================
  LocalScript — Multi-Agent Lua Generator
============================================================
  Task      : write a fibonacci function with memoization
  Backend   : openrouter
  Max iters : 3
  Session   : workspace/session_20260403_143022
============================================================

[Generator] Iteration 1 — 342 chars written
[Validator] ✓ Code OK
[Reviewer] ✓ Approved

============================================================
  ✓ SUCCESS in 1 iteration(s)
  Output: workspace/session_20260403_143022/final.lua
============================================================
```

---

## 🤖 LLM-бэкенды

Поддерживается 4 бэкенда. Настройка в `.env`:

| Бэкенд | Конфигурация | API-ключ |
|--------|-------------|:---:|
| **OpenRouter** (рекомендуется) | `LLM_BACKEND=openrouter` | ✅ `OPENROUTER_API_KEY` |
| **OpenAI** | `LLM_BACKEND=openai` | ✅ `OPENAI_API_KEY` |
| **Anthropic** | `LLM_BACKEND=anthropic` | ✅ `ANTHROPIC_API_KEY` |
| **Ollama** (локально) | `LLM_BACKEND=ollama` | ❌ Бесплатно |

### Локальный режим (без API-ключа)

```bash
# Установите Ollama: https://ollama.ai
ollama pull qwen2.5-coder:7b

LLM_BACKEND=ollama LLM_MODEL=qwen2.5-coder:7b python main.py --task "write quicksort"
```

### Гибридный режим (разные модели для агентов)

Каждый агент может использовать свою модель. Настройка в `config/settings.yaml`:

```yaml
agents:
  generator:
    backend: ollama
    model: qwen2.5-coder:7b      # локальная модель для генерации
  validator:
    backend: ollama
    model: qwen2.5-coder:7b      # локальная модель для анализа ошибок
  reviewer:
    backend: openrouter
    model: openai/gpt-4o-mini    # облачная модель для ревью
```

Если для агента нет переопределения, используется дефолтный `llm:` из конфига.

---

## 🧠 Reasoning-стратегии

Опциональные **стратегии рассуждения** улучшают качество кода через многошаговое мышление LLM. Стратегия применяется *перед* первой генерацией кода (при ретраях используется прямой вызов для скорости).

| Стратегия | LLM-вызовов | Как работает | Лучше всего для |
|-----------|:-----------:|--------------|-----------------|
| `none` | 1 | Прямой вызов (по умолчанию, нулевой overhead) | Быстрая итерация, малые модели |
| `reflect` | 3 | Генерация → самокритика → ревизия | Ловля багов до валидации |
| `cot` | 2 | Пошаговое рассуждение → генерация кода | Алгоритмические задачи, сложная логика |

### Как включить

В `config/settings.yaml`:

```yaml
strategy:
  generator: reflect    # или "cot", "none"
```

Или через переменную окружения:

```bash
GENERATOR_STRATEGY=reflect python main.py --task "write a binary search tree"
```

### Как это работает

**`reflect`** (3 вызова LLM):
```
Задача → [LLM: напиши код] → черновик
       → [LLM: найди баги]  → критика
       → [LLM: исправь]     → финальный код → в Validator
```

**`cot`** (2 вызова LLM):
```
Задача → [LLM: продумай алгоритм, структуры, edge cases] → план
       → [LLM: напиши код по плану]                       → код → в Validator
```

> **Совет**: На бесплатных API с rate limits используйте `none`. На локальном Ollama с моделями 30B+ стратегия `reflect` даёт наибольший прирост качества.

---

## 🖥️ Интерфейсы

### CLI

```bash
python main.py --task "write a calculator"
python main.py --task-file examples/fibonacci.txt --output ./out/
python main.py --task "sort a table" --backend ollama --max-iterations 5
```

### Web UI

```bash
python api/server.py
# Откройте http://127.0.0.1:8000
```

Возможности:
- Ввод задачи с live-обновлениями статуса
- Браузер сессий с историей итераций
- Просмотр файлов с подсветкой синтаксиса
- WebSocket для прогресса в реальном времени
- Отображение финального Lua-кода

### REST API

```bash
python api/server.py
```

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/api/run-task` | Запуск pipeline, возвращает `session_id` |
| `GET` | `/api/session/{id}` | Статус сессии, итерация, ошибки |
| `GET` | `/api/sessions` | Список всех сессий |
| `GET` | `/api/session/{id}/files` | Файлы в папке сессии |
| `GET` | `/api/session/{id}/final` | Финальный Lua-код |
| `WS` | `/api/ws/{id}` | Live WebSocket обновления |

### 🔌 MCP-сервер

LocalScript — это [Model Context Protocol](https://modelcontextprotocol.io/) сервер. Любой MCP-совместимый AI-клиент может использовать его как инструмент.

```bash
pip install "mcp[cli]>=1.2.0"
python mcp_server/server.py
```

**Инструменты** (AI-клиенты вызывают наш pipeline):

| Инструмент | Описание |
|------------|----------|
| `generate_lua(task)` | Полный pipeline: генерация → валидация → ревью → код |
| `validate_lua(code)` | Проверка Lua-кода через `luac` + `lua` |
| `review_lua(code, task)` | AI-ревью кода |
| `fix_lua(code, errors)` | Исправление кода по сообщениям об ошибках |

**Ресурсы** (AI-клиенты читают наши данные):

| Ресурс | Описание |
|--------|----------|
| `sessions://list` | Все сессии workspace |
| `session://{id}/status` | Статус сессии + отчёт |
| `session://{id}/final.lua` | Сгенерированный Lua-код |

**Подключение к Claude Desktop** — добавьте в `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "localscript": {
      "command": "python",
      "args": ["mcp_server/server.py"],
      "cwd": "/path/to/localscript"
    }
  }
}
```

Также работает с: **Cursor**, **VS Code Copilot**, **Continue.dev**, **Cline**, **Windsurf**, **Zed**.

LocalScript может **использовать внешние MCP-инструменты** — настройка в `settings.yaml`:
```yaml
mcp_tools:
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
```

---

## 📁 Вывод сессии

Каждый запуск создаёт сессию с таймстампом:

```
workspace/session_20260403_143022/
├── task.txt                 # описание задачи
├── iteration_1.lua          # первая попытка
├── iteration_1_errors.txt   # ошибки (если есть)
├── iteration_2.lua          # вторая попытка (если ретрай)
├── final.lua                # ✅ одобренный код
└── report.md                # отчёт ревьюера
```

---

## 📂 Структура проекта

```
localscript/
├── agents/                  # AI-агенты
│   ├── base.py              # BaseAgent: промпты, LLM-вызовы, стратегии, стоп-сигнал
│   ├── generator.py         # Пишет Lua-код, стратегия на первой попытке
│   ├── validator.py         # Запускает luac+lua, объясняет ошибки через LLM
│   └── reviewer.py          # Ревью кода, одобрение через <INFO> Finished
├── strategies/              # Reasoning-стратегии (опционально)
│   ├── base.py              # ReasoningStrategy ABC + PassthroughStrategy
│   ├── reflect.py           # Генерация → самокритика → ревизия
│   ├── cot.py               # Chain-of-thought: рассуждение → код
│   └── registry.py          # Реестр стратегий + фабрика
├── graph/                   # LangGraph pipeline
│   ├── state.py             # AgentState TypedDict
│   ├── nodes.py             # Функции нод с инъекцией LLM
│   └── pipeline.py          # Сборка StateGraph, run_pipeline()
├── llm/                     # Провайдеры LLM
│   ├── factory.py           # get_llm(role) — выбор модели по агенту
│   ├── openai_provider.py
│   ├── openrouter_provider.py
│   ├── anthropic_provider.py
│   └── ollama_provider.py
├── tools/
│   └── lua_runner.py        # LuaRunner: компиляция, выполнение, таймаут
├── api/                     # FastAPI веб-сервер
│   ├── server.py            # Фабрика приложения, статика, точка входа
│   ├── routes.py            # REST + WebSocket эндпоинты
│   └── models.py            # Pydantic-схемы запросов/ответов
├── mcp_server/              # MCP-сервер
│   ├── server.py            # Инструменты + Ресурсы + MCP-клиент
│   └── claude_desktop_config.json
├── frontend/                # Web UI
│   ├── index.html           # Дашборд — ввод задачи, список сессий
│   ├── session.html         # Просмотр сессии — статус, файлы, код
│   └── app.js               # Общие утилиты
├── config/
│   ├── settings.yaml        # Бэкенд, модели, таймауты, стратегии, MCP
│   └── agents.yaml          # Системные промпты для каждого агента
├── tests/                   # 48 тестов
├── examples/                # Примеры задач
├── main.py                  # CLI точка входа
├── Makefile                 # Шорткаты
└── docs/architecture.md     # Подробная документация архитектуры
```

---

## ⚙️ Конфигурация

### `config/settings.yaml`

```yaml
llm:
  backend: openrouter           # openai | ollama | openrouter | anthropic
  model: openai/gpt-4o-mini
  temperature: 0.2

agents:                         # переопределения по агентам (опционально)
  generator:
    # backend: ollama
    # model: qwen2.5-coder:7b

strategy:                       # reasoning-стратегии (опционально)
  generator: none               # "none" | "reflect" | "cot"

pipeline:
  max_iterations: 3
  execution_timeout: 10         # секунды на выполнение lua

workspace:
  base_dir: workspace
```

### `config/agents.yaml`

Системные промпты для каждого агента. Ключевые ограничения:
- **Generator**: выводит только чистый Lua (без markdown), стандартный Lua 5.3+ (без внешних фреймворков)
- **Validator**: различает реальные баги и намеренную обработку ошибок
- **Reviewer**: проверяет корректность, автономность выполнения, Lua-идиомы

### `.env`

API-ключи и переопределения бэкенда. См. `.env.example` для всех опций.

---

## 🧪 Тестирование

```bash
pytest tests/ -v
```

```
tests/test_agents.py      15 passed  — generator, validator, reviewer, strip_code_fences
tests/test_lua_runner.py    9 passed  — compile, execute, timeout, error files
tests/test_pipeline.py      9 passed  — conditional edges, end-to-end с mock LLM
tests/test_strategies.py  15 passed  — reflect, cot, registry, интеграция с агентами
────────────────────────────────────
                           48 passed ✅
```

Все тесты используют mock LLM — API-ключи не нужны.

---

## 🛠️ Makefile

```bash
make run                    # запуск с дефолтной задачей
make task TASK="sort table" # запуск с кастомной задачей
make local                  # запуск с Ollama (без API-ключа)
make test                   # запуск всех тестов
make clean                  # удаление сессий workspace
make graph                  # вывод mermaid-диаграммы графа
```

---

## 📋 Требования

- **Python** 3.11+
- **Lua** 5.3+ с `luac` (`apt install lua5.4` / `brew install lua` / `scoop install lua`)
- **API-ключ** для OpenRouter/OpenAI/Anthropic, **или** [Ollama](https://ollama.ai) для локального режима

---

## 🏗️ Архитектура

```
START
  │
  ▼
[generate] ──────────────────────────────┐
  │  (стратегия: reflect/cot/none)       │ (ошибки + бюджет ретраев)
  ▼                                       │
[validate] ──── ошибки? ─────────────────┘
  │
  │ код OK
  ▼
[review] ──── нужны доработки? ──────────┐
  │                                       │
  │ <INFO> Finished                       │ (повторная генерация с фидбеком)
  ▼                                       │
 END ◄────────────────────────────────────┘
  ▲
  │ (max_iterations достигнут)
[fail] ──────────────────────────────────►END
```

Подробнее: [docs/architecture.md](docs/architecture.md)

---

## 📄 Лицензия

MIT

---

<div align="center">
<sub>Построен на <a href="https://github.com/langchain-ai/langgraph">LangGraph</a> · Вдохновлён <a href="https://github.com/OpenBMB/ChatDev">ChatDev</a></sub>
</div>
