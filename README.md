<div align="center">

# ⚡ LocalScript

**Autonomous multi-agent AI system for generating and validating Lua code**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-66%20passed-brightgreen.svg)](#-testing)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](#-mcp-server)

Describe a task in plain English — get working, reviewed Lua code.

**CLI** · **Web UI** · **REST API** · **MCP Server**

</div>

---

## What Makes This Different

LocalScript **actually runs your code**. Three AI agents collaborate in a loop:

```
┌──────────┐     ┌───────────┐     ┌──────────┐
│ Generator│────▶│ Validator  │────▶│ Reviewer  │
│ write Lua│     │ luac + lua │     │ quality   │
└──────────┘     └───────────┘     └──────────┘
     ▲                │                  │
     │    errors      │     feedback     │
     └────────────────┘                  │
     └───────────────────────────────────┘
```

- **Generator** — writes Lua code from task description (optionally with a reasoning strategy)
- **Validator** — compiles with `luac` and executes with `lua` — real errors, not hallucinated ones
- **Reviewer** — checks code quality, approves or requests improvements
- The loop retries up to `max_iterations` times, saving each attempt

Inspired by [ChatDev](https://github.com/OpenBMB/ChatDev), but with **real code execution** instead of simulated testing.

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/Podtverzhdeno/LocalScripts_AI
cd LocalScripts_AI
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — add your API key (see "LLM Backends" below)
```

### 3. Run

```bash
python main.py --task "write a fibonacci function with memoization"
```

Output:
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

## 🤖 LLM Backends

4 backends supported. Configure in `.env`:

| Backend | Config | API Key |
|---------|--------|:---:|
| **OpenRouter** (recommended) | `LLM_BACKEND=openrouter` | ✅ `OPENROUTER_API_KEY` |
| **OpenAI** | `LLM_BACKEND=openai` | ✅ `OPENAI_API_KEY` |
| **Anthropic** | `LLM_BACKEND=anthropic` | ✅ `ANTHROPIC_API_KEY` |
| **Ollama** (local) | `LLM_BACKEND=ollama` | ❌ Free |

### Local mode (no API key)

```bash
# Install Ollama: https://ollama.ai
ollama pull qwen2.5-coder:7b

LLM_BACKEND=ollama LLM_MODEL=qwen2.5-coder:7b python main.py --task "write quicksort"
```

### Hybrid mode (per-agent models)

Each agent can use its own model. Configure in `config/settings.yaml`:

```yaml
agents:
  generator:
    backend: ollama
    model: qwen2.5-coder:7b      # local model for code generation
  validator:
    backend: ollama
    model: qwen2.5-coder:7b      # local model for error analysis
  reviewer:
    backend: openrouter
    model: openai/gpt-4o-mini    # cloud model for code review
```

If no override is set for an agent, the default `llm:` config is used.

---

## 🧠 Reasoning Strategies

Optional **reasoning strategies** improve code quality through multi-step LLM reasoning. A strategy is applied *before* the first code generation (retries use direct calls for speed).

| Strategy | LLM Calls | How It Works | Best For |
|----------|:---------:|--------------|----------|
| `none` | 1 | Direct call (default, zero overhead) | Fast iteration, small models |
| `reflect` | 3 | Generate → self-critique → revise | Catching bugs before validation |
| `cot` | 2 | Reason step-by-step → generate code | Algorithmic tasks, complex logic |

### How to enable

In `config/settings.yaml`:

```yaml
strategy:
  generator: reflect    # or "cot", "none"
```

Or via environment variable:

```bash
GENERATOR_STRATEGY=reflect python main.py --task "write a binary search tree"
```

### How it works

**`reflect`** (3 LLM calls):
```
Task → [LLM: write code]      → draft
     → [LLM: find bugs]       → critique
     → [LLM: fix issues]      → final code → to Validator
```

**`cot`** (2 LLM calls):
```
Task → [LLM: plan algorithm, structures, edge cases] → plan
     → [LLM: write code from plan]                   → code → to Validator
```

> **Tip**: On free-tier APIs with rate limits, use `none`. On local Ollama with 30B+ models, `reflect` gives the best quality improvement.

---

## 🔒 Sandbox

Generated Lua code runs in a **sandbox** that blocks dangerous system calls. Enabled by default.

| Blocked | Allowed |
|---------|--------|
| `os.execute`, `os.remove`, `os.rename`, `os.exit` | `os.clock`, `os.date`, `os.time` |
| `io.popen`, `io.open` | `io.read`, `io.write`, `io.stdout` |
| `require`, `loadfile`, `dofile`, `package` | `print`, `type`, `tostring`, `pcall` |
| `debug.*`, `rawset` | `string.*`, `table.*`, `math.*`, `coroutine.*` |

Disable in `config/settings.yaml` if needed:
```yaml
pipeline:
  sandbox: false    # ⚠️ not recommended — allows arbitrary system access
```

---

## 🖥️ Interfaces

### CLI

```bash
python main.py --task "write a calculator"
python main.py --task-file examples/fibonacci.txt --output ./out/
python main.py --task "sort a table" --backend ollama --max-iterations 5
```

### Web UI

```bash
python api/server.py
# Open http://127.0.0.1:8000
```

Features:
- Task input with live status updates
- Session browser with iteration history
- File viewer with syntax highlighting
- WebSocket real-time progress
- Final Lua code display

### REST API

```bash
python api/server.py
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/run-task` | Start pipeline, returns `session_id` |
| `GET` | `/api/session/{id}` | Session status, iteration, errors |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/session/{id}/files` | Files in session folder |
| `GET` | `/api/session/{id}/final` | Final Lua code |
| `WS` | `/api/ws/{id}` | Live WebSocket updates |

### 🔌 MCP Server

LocalScript is a [Model Context Protocol](https://modelcontextprotocol.io/) server. Any MCP-compatible AI client can use it as a tool.

```bash
pip install "mcp[cli]>=1.2.0"
python mcp_server/server.py
```

**Tools** (AI clients call our pipeline):

| Tool | Description |
|------|-------------|
| `generate_lua(task)` | Full pipeline: generate → validate → review → return code |
| `validate_lua(code)` | Check Lua code with `luac` + `lua` |
| `review_lua(code, task)` | AI code review |
| `fix_lua(code, errors)` | Fix broken code given error messages |

**Resources** (AI clients read our data):

| Resource | Description |
|----------|-------------|
| `sessions://list` | All workspace sessions |
| `session://{id}/status` | Session status + report |
| `session://{id}/final.lua` | Generated Lua code |

**Connect to Claude Desktop** — add to `claude_desktop_config.json`:
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

Also works with: **Cursor**, **VS Code Copilot**, **Continue.dev**, **Cline**, **Windsurf**, **Zed**.

LocalScript can also **use external MCP tools** via [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) — configure in `settings.yaml`:
```yaml
mcp_tools:
  # Stdio transport (launches subprocess)
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    transport: stdio

  # HTTP transport (connects to running server)
  - name: remote_tools
    url: "http://localhost:8000/mcp"
    transport: http
```

---

## 📁 Session Output

Every run creates a timestamped session:

```
workspace/session_20260403_143022/
├── task.txt                 # original task description
├── iteration_1.lua          # first attempt
├── iteration_1_errors.txt   # errors (if any)
├── iteration_2.lua          # second attempt (if retry)
├── final.lua                # ✅ approved code
└── report.md                # reviewer summary
```

---

## 📂 Project Structure

```
localscript/
├── agents/                  # AI agents
│   ├── base.py              # BaseAgent: prompts, LLM calls, strategies, stop signal
│   ├── generator.py         # Writes Lua code, uses strategy on first attempt
│   ├── validator.py         # Runs luac+lua, explains errors via LLM
│   └── reviewer.py          # Code review, <INFO> Finished approval
├── strategies/              # Reasoning strategies (optional)
│   ├── base.py              # ReasoningStrategy ABC + PassthroughStrategy
│   ├── reflect.py           # Generate → self-critique → revise
│   ├── cot.py               # Chain-of-thought: reason, then code
│   └── registry.py          # Strategy registry + factory
├── graph/                   # LangGraph pipeline
│   ├── state.py             # AgentState TypedDict
│   ├── nodes.py             # Node functions with per-agent LLM injection
│   └── pipeline.py          # StateGraph assembly, run_pipeline()
├── llm/                     # LLM backend providers
│   ├── factory.py           # get_llm(role) — per-agent model selection
│   ├── openai_provider.py
│   ├── openrouter_provider.py
│   ├── anthropic_provider.py
│   └── ollama_provider.py
├── tools/
│   ├── lua_runner.py        # LuaRunner: compile, execute, timeout, sandbox
│   └── sandbox.py           # Lua sandbox: blocks os.execute, io.popen, require, debug
├── api/                     # FastAPI web server
│   ├── server.py            # App factory, static files, entry point
│   ├── routes.py            # REST + WebSocket endpoints
│   └── models.py            # Pydantic request/response schemas
├── mcp_server/              # MCP server
│   ├── server.py            # Tools + Resources + MCP client
│   └── claude_desktop_config.json
├── frontend/                # Web UI
│   ├── index.html           # Dashboard — task input, session list
│   ├── session.html         # Session viewer — status, files, code
│   └── app.js               # Shared utilities
├── config/
│   ├── settings.yaml        # Backend, models, timeouts, strategies, MCP tools
│   └── agents.yaml          # System prompts for each agent
├── tests/                   # 66 tests
├── examples/                # Example task files
├── main.py                  # CLI entry point
├── Makefile                 # Shortcuts
└── docs/architecture.md     # Detailed architecture docs
```

---

## ⚙️ Configuration

### `config/settings.yaml`

```yaml
llm:
  backend: openrouter           # openai | ollama | openrouter | anthropic
  model: openai/gpt-4o-mini
  temperature: 0.2

agents:                         # per-agent overrides (optional)
  generator:
    # backend: ollama
    # model: qwen2.5-coder:7b

strategy:                       # reasoning strategies (optional)
  generator: none               # "none" | "reflect" | "cot"

pipeline:
  max_iterations: 3
  execution_timeout: 10         # seconds for lua execution
  sandbox: true                 # block os.execute, io.popen, require, debug

workspace:
  base_dir: workspace
```

### `config/agents.yaml`

System prompts for each agent. Key constraints:
- **Generator**: outputs raw Lua only (no markdown), standard Lua 5.3+ (no external frameworks)
- **Validator**: distinguishes real bugs from intentional error handling
- **Reviewer**: checks correctness, standalone execution, Lua idioms

### `.env`

API keys and backend overrides. See `.env.example` for all options.

---

## 🧪 Testing

```bash
pytest tests/ -v
```

```
tests/test_agents.py      15 passed  — generator, validator, reviewer, strip_code_fences
tests/test_lua_runner.py    9 passed  — compile, execute, timeout, error files
tests/test_pipeline.py      9 passed  — conditional edges, end-to-end with mock LLM
tests/test_strategies.py  15 passed  — reflect, cot, registry, agent integration
tests/test_sandbox.py     18 passed  — blocked calls, safe functions, sandbox toggle
────────────────────────────────────
                           66 passed ✅
```

All tests use mock LLMs — no API keys needed.

---

## 🛠️ Makefile

```bash
make run                    # run with default task
make task TASK="sort table" # run with custom task
make local                  # run with Ollama (no API key)
make test                   # run all tests
make clean                  # remove workspace sessions
make graph                  # print mermaid graph diagram
```

---

## 📋 Requirements

- **Python** 3.11+
- **Lua** 5.3+ with `luac` (`apt install lua5.4` / `brew install lua` / `scoop install lua`)
- **API key** for OpenRouter/OpenAI/Anthropic, **or** [Ollama](https://ollama.ai) for local mode

---

## 🏗️ Architecture

```
START
  │
  ▼
[generate] ──────────────────────────────┐
  │  (strategy: reflect/cot/none)        │ (errors + retry budget left)
  ▼                                       │
[validate] ──── errors? ─────────────────┘
  │
  │ code OK
  ▼
[review] ──── needs improvements? ───────┐
  │                                       │
  │ <INFO> Finished                       │ (re-enter generate with feedback)
  ▼                                       │
 END ◄────────────────────────────────────┘
  ▲
  │ (max_iterations reached)
[fail] ──────────────────────────────────►END
```

See [docs/architecture.md](docs/architecture.md) for full details.

---

## 📄 License

MIT

---

<div align="center">
<sub>Built with <a href="https://github.com/langchain-ai/langgraph">LangGraph</a> · Inspired by <a href="https://github.com/OpenBMB/ChatDev">ChatDev</a></sub>
</div>
