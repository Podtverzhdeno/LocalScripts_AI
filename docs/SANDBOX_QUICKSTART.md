# Sandbox Feature — Quick Start

## Overview

LocalScript now supports **three sandbox modes** for executing Lua code:

1. **`lua`** (default) — Lua-level isolation, blocks dangerous functions
2. **`docker`** — Full container isolation with resource limits
3. **`none`** — No sandbox (unsafe, testing only)

## Usage

### CLI

```bash
# Default: Lua sandbox
python main.py --task "write fibonacci"

# Docker sandbox (maximum security)
python main.py --task "write fibonacci" --sandbox docker

# No sandbox (unsafe)
python main.py --task "write fibonacci" --sandbox none
```

### Makefile

```bash
# Run with Docker sandbox
make docker TASK="write fibonacci"

# Build Docker image
make docker-sandbox-build

# Test Docker sandbox
make docker-sandbox-test
```

### Configuration

**settings.yaml:**
```yaml
pipeline:
  sandbox_mode: lua  # "lua" | "docker" | "none"
```

**Environment variable:**
```bash
export SANDBOX_MODE=docker
python main.py --task "your task"
```

## Security Comparison

| Feature | Lua Sandbox | Docker Sandbox |
|---------|-------------|----------------|
| Blocks `os.execute` | ✅ | ✅ |
| Blocks file I/O | ✅ | ✅ |
| Network isolation | ❌ | ✅ |
| Memory limits | ❌ | ✅ (128MB) |
| CPU limits | ❌ | ✅ (50%) |
| Metatable protection | ✅ | N/A |
| Performance | Fast | ~100-200ms overhead |

## What's Blocked

### Lua Sandbox

- System: `os.execute`, `os.remove`, `os.rename`, `os.exit`, `os.getenv`
- File I/O: `io.popen`, `io.open` (write mode)
- Code loading: `require`, `loadfile`, `dofile`, `load`
- Introspection: `debug.*`
- Environment: `rawset`, `setfenv`, `getfenv`

### Docker Sandbox

All of the above, plus:
- No network access
- Limited memory (128MB)
- Limited CPU (50% of one core)
- Read-only filesystem

## Testing

```bash
# Test Lua sandbox
pytest tests/test_sandbox_enhanced.py -v

# Test Docker sandbox (requires Docker)
pytest tests/test_docker_sandbox.py -v

# Test all
pytest tests/ -v
```

## Documentation

- Full security guide: `docs/SECURITY.md`
- Implementation details: `tools/sandbox.py`, `tools/docker_sandbox.py`

## Requirements

- **Lua sandbox:** Lua 5.3+ (already required)
- **Docker sandbox:** Docker installed and running

## Examples

```bash
# Safe execution with Lua sandbox
python main.py --task "write a calculator with error handling"

# Maximum security for untrusted code
python main.py --task "parse user input" --sandbox docker

# Quick test without sandbox (development only)
python main.py --task "test script" --sandbox none
```

## Troubleshooting

**Docker not found:**
```bash
# Install Docker
# Linux: sudo apt install docker.io
# macOS/Windows: https://www.docker.com/products/docker-desktop
```

**Docker daemon not running:**
```bash
# Start Docker
# Linux: sudo systemctl start docker
# macOS/Windows: Start Docker Desktop
```

**Build Docker image:**
```bash
make docker-sandbox-build
# or
docker build -f Dockerfile.sandbox -t localscript-lua-sandbox .
```
