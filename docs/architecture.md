# LocalScript Architecture

Multi-agent Lua code generation system built with LangGraph.  
Inspired by [ChatDev](https://github.com/OpenBMB/ChatDev) — but using real code execution instead of simulated testing.

## Key Difference from ChatDev

ChatDev uses a custom YAML-driven conversation engine. LocalScript replaces that with:
- **LangGraph `StateGraph`** — explicit graph with conditional edges
- **Real `luac` + `lua` execution** — actual compilation and runtime errors feed back into the generator
- **Dependency injection** — LLM passed into the graph at build time, trivial to mock in tests

---

## Graph Flow

```
START
  │
  ▼
[generate] ──────────────────────────────┐
  │                                       │ (errors + retry budget left)
  ▼                                       │
[validate] ──── errors? ─────────────────┘
  │
  │ code OK
  ▼
[review] ──── needs improvements? ───────┐
  │                                       │
  │ <INFO> Finished                       │ (re-enter generate with review feedback)
  ▼                                       │
 END ◄────────────────────────────────────┘
  ▲
  │ (max_iterations reached at any point)
[fail] ──────────────────────────────────►END
```

### Conditional edges

| Source     | Condition                          | Destination |
|------------|------------------------------------|-------------|
| `validate` | `status == "reviewing"`            | `review`    |
| `validate` | `status == "generating"`           | `generate`  |
| `validate` | `iterations >= max_iterations`     | `fail`      |
| `review`   | `status == "done"`                 | `END`       |
| `review`   | `status == "generating"`           | `generate`  |
| `review`   | `iterations >= max_iterations`     | `fail`      |

---

## Component Overview

### `agents/`

| File           | Role                                                                 |
|----------------|----------------------------------------------------------------------|
| `base.py`      | `BaseAgent`: loads system prompt from YAML, wraps LLM, stop signal  |
| `generator.py` | Writes Lua code; on retry, receives error/review context             |
| `validator.py` | Runs `luac`+`lua`; uses LLM to explain errors in plain language      |
| `reviewer.py`  | Quality review; emits `<INFO> Finished` to approve or requests fixes |

### `graph/`

| File          | Role                                                  |
|---------------|-------------------------------------------------------|
| `state.py`    | `AgentState` TypedDict — shared state across all nodes |
| `nodes.py`    | Pure node functions — created via `make_nodes(llm)` closure |
| `pipeline.py` | `StateGraph` assembly, conditional edges, `run_pipeline()` |

### `tools/`

| File           | Role                                                         |
|----------------|--------------------------------------------------------------|
| `lua_runner.py`| `LuaRunner`: compile with `luac`, execute with `lua`, timeout, save iterations to workspace |

### `llm/`

| File          | Role                                         |
|---------------|----------------------------------------------|
| `factory.py`  | `get_llm()` — returns OpenAI or Ollama backend based on env/config |

---

## Workspace Layout

Each run creates a timestamped session directory:

```
workspace/
└── session_20250402_143022/
    ├── task.txt              # original task
    ├── iteration_1.lua       # first attempt
    ├── iteration_1_errors.txt
    ├── iteration_2.lua       # after fix
    ├── final.lua             # approved code ✅
    └── report.md             # reviewer summary
```

---

## ChatDev Patterns Used

| ChatDev concept         | LocalScript equivalent                          |
|-------------------------|-------------------------------------------------|
| `loop_counter` node     | `iterations` / `max_iterations` in `AgentState` |
| `<INFO> Finished` stop  | `BaseAgent.is_finished()` + `STOP_SIGNAL`       |
| `literal` prompt nodes  | `config/agents.yaml` system prompts             |
| `carry_data`            | LangGraph `AgentState` TypedDict                |
| `clear_context`         | `errors=None, review=None` reset in node output |

---

## Running Locally

```bash
# OpenAI
cp .env.example .env
# fill OPENAI_API_KEY in .env
python main.py --task "write a fibonacci function"

# Ollama
LLM_BACKEND=ollama LLM_MODEL=llama3.2 python main.py --task "write quicksort"

# From file
python main.py --task-file examples/fibonacci.txt --output ./out/
```
