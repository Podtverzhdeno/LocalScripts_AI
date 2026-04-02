# LocalScript 🤖→🌙

Multi-agent Lua code generation system powered by **LangGraph**.  
Describe a task in plain English — get working, reviewed Lua code.

Inspired by [ChatDev](https://github.com/OpenBMB/ChatDev), but with **real code execution**: actual `luac` compilation and `lua` runtime errors feed back into the generator loop.

---

## How it works

```
[Generator] → writes Lua code
[Validator] → compiles with luac, runs with lua, explains errors via LLM
[Reviewer]  → quality review, approves or requests improvements
```

The graph retries up to `max_iterations` times before giving up. Each iteration is saved to a timestamped workspace session.

## Quickstart

```bash
git clone https://github.com/Podtverzhdeno/LocalScripts_AI
cd LocalScripts_AI

pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY

python main.py --task "write a fibonacci function"
```

**FRONTEND**

pip install fastapi "uvicorn[standard]" websockets  
  
python api/server.py  
    
**Local mode (no API key):**
```bash
# Requires Ollama running: https://ollama.ai
LLM_BACKEND=ollama LLM_MODEL=llama3.2 python main.py --task "write quicksort"
```

**From file:**
```bash
python main.py --task-file examples/fibonacci.txt --output ./out/
```

## Output

Every run creates a session folder:

```
workspace/session_20250402_143022/
├── task.txt
├── iteration_1.lua
├── iteration_1_errors.txt   # if there were errors
├── iteration_2.lua
├── final.lua                # ✅ approved code
└── report.md                # reviewer summary
```

## Makefile shortcuts

```bash
make run       # run with default task
make test      # run all tests
make local     # run with Ollama
make clean     # remove workspace sessions
make graph     # print mermaid graph diagram
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for full details.

```
START → generate → validate → review → END
                      ↑           ↓
                  (retry on errors / reviewer feedback)
                      └── fail → END (max iterations)
```

## Configuration

`config/settings.yaml` — backend, model, timeouts  
`config/agents.yaml` — system prompts for each agent  
`.env` — API keys and overrides

## Requirements

- Python 3.11+
- `lua5.4` + `luac` (`apt install lua5.4` / `brew install lua`)
- OpenAI API key **or** Ollama running locally

