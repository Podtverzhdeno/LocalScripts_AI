# Security Guide

LocalScript executes AI-generated Lua code. This guide explains the security measures in place and best practices.

## Sandbox Modes

### 1. Lua Sandbox (Default) — `--sandbox lua`

**How it works:**
- Injects a Lua preamble before user code
- Blocks dangerous functions by setting them to `nil` or error stubs
- Protects system tables with metatables
- Locks global environment after setup

**What's blocked:**
- System execution: `os.execute`, `os.remove`, `os.rename`, `os.exit`, `os.getenv`
- File I/O: `io.popen`, `io.open` (write mode)
- Code loading: `require`, `loadfile`, `dofile`, `load`, `package`
- Introspection: `debug.*` library
- Environment manipulation: `rawset`, `setfenv`, `getfenv`

**What's allowed:**
- Safe I/O: `io.read`, `io.write`, `io.stdout`, `io.stderr`
- Safe OS: `os.clock`, `os.date`, `os.time`, `os.difftime`
- Standard libraries: `string.*`, `table.*`, `math.*`, `coroutine.*`, `utf8.*`
- Core functions: `print`, `type`, `tostring`, `tonumber`, `error`, `assert`, `pcall`, `xpcall`

**Enhanced protection:**
```lua
-- Metatable protection prevents bypass
getmetatable(os)  -- returns nil (hidden)
os.execute = function() end  -- ERROR: Cannot modify os table

-- Global environment locked
print = function() end  -- ERROR: Cannot redefine global

-- setmetatable restricted on system tables
setmetatable(os, {})  -- ERROR: Cannot set metatable on protected tables
```

**Limitations:**
- Lua-level only — no OS-level isolation
- Vulnerable to Lua VM bugs (rare)
- No resource limits (CPU, memory)

**Use when:**
- Running trusted or reviewed code
- Performance is critical
- Docker not available

---

### 2. Docker Sandbox — `--sandbox docker`

**How it works:**
- Executes code in a disposable Alpine Linux container
- Minimal image (only Lua 5.4, no Python, no shell tools)
- Container destroyed after execution

**Security features:**
- **No network access:** `--network none`
- **Memory limit:** 128MB (configurable)
- **CPU limit:** 50% of one CPU (configurable)
- **Read-only filesystem:** Root FS is read-only
- **Writable /tmp:** 10MB, `noexec,nosuid` flags
- **Non-root user:** Runs as UID 1000
- **No new privileges:** `--security-opt no-new-privileges`

**Resource limits:**
```python
DockerConfig(
    memory_limit="128m",      # Max memory
    cpu_quota=50000,          # 50% of one CPU
    timeout=10,               # Execution timeout (seconds)
)
```

**Use when:**
- Running untrusted code
- Maximum security required
- DevOps/CI environments
- Multi-tenant systems

**Requirements:**
- Docker installed and running
- ~5MB disk space for image

---

### 3. No Sandbox — `--sandbox none`

**⚠️ UNSAFE — Testing only**

Executes code directly without restrictions. **Never use in production.**

---

## Setup

### Lua Sandbox (Default)

No setup required. Works out of the box.

```bash
python main.py --task "your task"  # Uses lua sandbox by default
```

### Docker Sandbox

1. Install Docker:
   - **Linux:** `sudo apt install docker.io` or `brew install docker`
   - **macOS/Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. Build sandbox image:
   ```bash
   make docker-sandbox-build
   # or manually:
   docker build -f Dockerfile.sandbox -t localscript-lua-sandbox .
   ```

3. Run with Docker sandbox:
   ```bash
   python main.py --task "your task" --sandbox docker
   # or via Makefile:
   make docker TASK="your task"
   ```

---

## Testing

### Test Lua Sandbox

```bash
pytest tests/test_sandbox_enhanced.py -v
```

Tests verify:
- Dangerous functions are blocked
- Safe functions work
- Metatable protection prevents bypass
- Global environment is locked

### Test Docker Sandbox

```bash
pytest tests/test_docker_sandbox.py -v
```

Tests verify:
- Docker execution works
- Timeouts are enforced
- Containers are destroyed
- Resource limits are applied

---

## Best Practices

### For Development

1. **Use Lua sandbox** for fast iteration
2. **Review generated code** before running
3. **Set execution timeout** to prevent infinite loops
4. **Monitor workspace directory** for unexpected files

### For Production

1. **Use Docker sandbox** for untrusted code
2. **Run in isolated environment** (VM, container)
3. **Limit API rate** to prevent abuse
4. **Log all executions** for audit trail
5. **Set resource limits** in Docker config

### For Multi-Tenant Systems

1. **Always use Docker sandbox**
2. **One container per execution** (already enforced)
3. **Separate workspace directories** per user
4. **Implement request quotas**
5. **Monitor resource usage**

---

## Configuration

### Via CLI

```bash
python main.py --task "task" --sandbox lua     # Lua sandbox
python main.py --task "task" --sandbox docker  # Docker sandbox
python main.py --task "task" --sandbox none    # No sandbox (unsafe)
```

### Via Config File

`config/settings.yaml`:
```yaml
pipeline:
  sandbox_mode: lua        # "lua" | "docker" | "none"
  execution_timeout: 10    # seconds
```

### Via Environment Variable

```bash
export SANDBOX_MODE=docker
python main.py --task "task"
```

---

## Troubleshooting

### Lua Sandbox

**Problem:** Code fails with `[SANDBOX] ... is blocked`

**Solution:** Code is trying to use a blocked function. This is expected behavior. Review the code and ensure it only uses safe functions.

### Docker Sandbox

**Problem:** `Docker not found`

**Solution:** Install Docker and ensure it's in PATH.

**Problem:** `Docker daemon is not running`

**Solution:** Start Docker Desktop or `sudo systemctl start docker`

**Problem:** `Failed to build Docker image`

**Solution:** Check `Dockerfile.sandbox` exists and Docker has internet access to pull Alpine base image.

**Problem:** Execution is slow

**Solution:** Docker has overhead (~100-200ms per execution). Use Lua sandbox for performance-critical tasks.

---

## Security Considerations

### What the Sandbox Protects Against

✅ System command execution (`os.execute`)  
✅ File system access (`io.open`, `loadfile`)  
✅ Network access (Docker mode only)  
✅ Resource exhaustion (Docker mode only)  
✅ Privilege escalation  
✅ Module loading (`require`)  

### What the Sandbox Does NOT Protect Against

❌ Lua VM bugs (use latest Lua version)  
❌ Logic bombs in generated code (review code)  
❌ Excessive CPU usage (Lua mode — use Docker for limits)  
❌ Memory exhaustion (Lua mode — use Docker for limits)  

### Defense in Depth

For maximum security, combine multiple layers:

1. **Sandbox:** Use Docker mode
2. **Network:** Run in isolated network
3. **Filesystem:** Mount workspace as read-only where possible
4. **Monitoring:** Log all executions
5. **Rate limiting:** Prevent abuse
6. **Code review:** Review generated code before production use

---

## Reporting Security Issues

Found a sandbox bypass? Please report responsibly:

1. **Do not** open a public GitHub issue
2. Email security details to the maintainers
3. Include proof-of-concept if possible
4. Allow time for a fix before public disclosure

---

## License

Security features are part of LocalScript and covered by the MIT license.
