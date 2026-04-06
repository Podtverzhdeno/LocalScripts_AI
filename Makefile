.PHONY: run test lint local install clean docker-sandbox-build docker-sandbox-test

# Run with OpenAI backend (default)
run:
	python main.py --task "write a fibonacci function in Lua"

# Run with custom task
task:
	python main.py --task "$(TASK)"

# Run with Ollama (local, no API key needed)
local:
	LLM_BACKEND=ollama python main.py --task "$(or $(TASK),write fibonacci in Lua)"

# Run with Docker sandbox (maximum security)
docker:
	python main.py --task "$(or $(TASK),write fibonacci in Lua)" --sandbox docker

# Build Docker sandbox image
docker-sandbox-build:
	docker build -f Dockerfile.sandbox -t localscript-lua-sandbox .

# Test Docker sandbox
docker-sandbox-test:
	pytest tests/test_docker_sandbox.py -v

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
coverage:
	pytest tests/ -v --tb=short

# Lint
lint:
	ruff check . || true

# Install dependencies
install:
	pip install -r requirements.txt

# Remove workspace sessions
clean:
	rm -rf workspace/session_*

# Remove Docker sandbox image
docker-clean:
	docker rmi localscript-lua-sandbox || true

# Show graph as mermaid diagram (requires langgraph installed)
graph:
	python -c "from graph.pipeline import build_pipeline; from unittest.mock import MagicMock; p = build_pipeline(MagicMock()); print(p.get_graph().draw_mermaid())"
