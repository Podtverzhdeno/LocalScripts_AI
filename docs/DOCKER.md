# 🐳 Docker Deployment Guide

Quick guide for running LocalScript with Docker Compose.

## Prerequisites

- Docker Desktop installed and running
- 8GB+ RAM available
- 10GB+ disk space (for Ollama model)

## Quick Start

### Linux/macOS:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Windows:
```cmd
scripts\setup.bat
```

### Manual:
```bash
# Start services
docker-compose up -d

# Pull Ollama model
docker exec localscript-ollama ollama pull qwen2.5-coder:7b

# Open browser
open http://localhost:8000
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| LocalScript Web UI | 8000 | Main application interface |
| LocalScript API | 8000/docs | FastAPI Swagger docs |
| Ollama | 11434 | Local LLM inference |

## Architecture

```
┌─────────────────────────────────────┐
│  LocalScript Container              │
│  - FastAPI Server (port 8000)       │
│  - RAG System (ChromaDB)            │
│  - Agent Pipeline                   │
│  - Lua Runtime                      │
└──────────────┬──────────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────────┐
│  Ollama Container                   │
│  - qwen2.5-coder:7b (7B params)     │
│  - API Server (port 11434)          │
└─────────────────────────────────────┘
```

## Configuration

Environment variables in `docker-compose.yml`:

```yaml
environment:
  - LLM_BACKEND=ollama
  - OLLAMA_BASE_URL=http://ollama:11434
  - LLM_MODEL=qwen2.5-coder:7b
```

## GPU Support (Optional)

Uncomment in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Requires:
- NVIDIA GPU
- NVIDIA Docker runtime installed

## Volumes

| Volume | Purpose |
|--------|---------|
| `./workspace` | Generated code sessions |
| `./config` | Configuration files |
| `./.veai` | RAG vector database |
| `ollama_data` | Ollama models cache |

## Common Commands

### View logs:
```bash
docker-compose logs -f
docker-compose logs -f localscript  # Only app logs
docker-compose logs -f ollama       # Only Ollama logs
```

### Restart services:
```bash
docker-compose restart
```

### Stop services:
```bash
docker-compose down
```

### Clean everything (including volumes):
```bash
docker-compose down -v
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

## Troubleshooting

### Ollama not responding:
```bash
# Check Ollama health
docker exec localscript-ollama curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama
```

### Model not found:
```bash
# Pull model manually
docker exec localscript-ollama ollama pull qwen2.5-coder:7b

# List available models
docker exec localscript-ollama ollama list
```

### RAG database not initialized:
```bash
# Initialize manually
docker exec localscript-app python -m rag.cli init

# Check stats
docker exec localscript-app python -m rag.cli stats
```

### Port already in use:
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Out of memory:
```bash
# Increase Docker memory limit in Docker Desktop settings
# Recommended: 8GB+ for Ollama + LocalScript
```

## Performance

### Expected resource usage:
- **CPU**: 2-4 cores
- **RAM**: 6-8 GB (4GB for Ollama, 2-4GB for LocalScript)
- **Disk**: ~10 GB (model + dependencies)

### Generation speed:
- **With GPU**: 50-100 tokens/sec
- **CPU only**: 5-15 tokens/sec

## Development

### Run with local code changes:
```bash
# Mount local code
docker-compose up -d

# Code changes auto-reload (if using --reload in server.py)
```

### Access container shell:
```bash
docker exec -it localscript-app bash
docker exec -it localscript-ollama bash
```

### Test API:
```bash
curl http://localhost:8000/api/sessions
curl -X POST http://localhost:8000/api/run-task \
  -H "Content-Type: application/json" \
  -d '{"task": "write fibonacci function"}'
```

## Production Deployment

For production use:

1. **Use external Ollama** (separate server with GPU)
2. **Add reverse proxy** (nginx/traefik)
3. **Enable HTTPS**
4. **Set resource limits**
5. **Configure logging**
6. **Add monitoring** (Prometheus/Grafana)

Example with external Ollama:
```yaml
localscript:
  environment:
    - OLLAMA_BASE_URL=https://ollama.your-domain.com
```

## MTS Hackathon Notes

For demo/presentation:

1. **Pre-pull model** before demo:
   ```bash
   docker exec localscript-ollama ollama pull qwen2.5-coder:7b
   ```

2. **Warm up system** with test request:
   ```bash
   curl -X POST http://localhost:8000/api/run-task \
     -H "Content-Type: application/json" \
     -d '{"task": "validate email"}'
   ```

3. **Check logs** are clean:
   ```bash
   docker-compose logs --tail=50
   ```

4. **Verify RAG** is initialized:
   ```bash
   docker exec localscript-app python -m rag.cli stats
   # Should show: Documents: 39
   ```

---

**Created for MTS True Tech Hack 2026**  
**Track:** Agent System for Lua Code Generation
