"""
Lua code execution tool.
Runs luac (compile check) and lua (execute) in a sandboxed subprocess.
Writes each iteration to the session workspace directory.

Sandbox modes:
  - 'lua' (default): Lua-level sandbox blocks dangerous system calls
    (os.execute, io.popen, loadfile, dofile, require, debug, etc.)
  - 'docker': Full isolation in disposable Docker container
    (no network, limited resources, read-only filesystem)
  - 'none': No sandbox (UNSAFE — for testing only)

See tools/sandbox.py for Lua sandbox details.
See tools/docker_sandbox.py for Docker sandbox details.
"""

import os
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tools.sandbox import wrap_in_sandbox

SandboxMode = Literal["lua", "docker", "none"]

# luac -o needs a null device; /dev/null doesn't exist on Windows
_NULL_DEVICE = "NUL" if os.name == "nt" else "/dev/null"


@dataclass
class LuaResult:
    success: bool
    stdout: str
    stderr: str
    timed_out: bool = False
    compiled_ok: bool = False  # True if luac passed (syntax is valid)
    execution_time: float = 0.0  # Execution time in seconds
    memory_used: int = 0  # Memory used in KB (if available)

    @property
    def errors(self) -> str:
        """Return combined error output."""
        return self.stderr.strip()

    @property
    def has_output(self) -> bool:
        """True if the script produced stdout before failing."""
        return bool(self.stdout.strip())

    @property
    def is_intentional_error(self) -> bool:
        """
        Heuristic: code compiled OK, produced output, then hit a runtime error.
        This pattern indicates intentional error handling demonstration
        (e.g. `error("Division by zero")` in a calculator).
        """
        return self.compiled_ok and self.has_output and not self.success and not self.timed_out

    def __str__(self) -> str:
        profile_info = ""
        if self.execution_time > 0:
            profile_info = f"\n[Profile] Time: {self.execution_time:.3f}s, Memory: {self.memory_used}KB"

        if self.success:
            return f"OK{profile_info}\n{self.stdout}" if self.stdout else f"OK{profile_info}"
        if self.timed_out:
            return f"TIMEOUT\n{self.stderr}"
        if self.is_intentional_error:
            return f"OK_WITH_EXPECTED_ERROR{profile_info}\n{self.stdout}\n---\n{self.stderr}"
        return f"ERROR\n{self.stderr}"


class LuaRunner:
    """
    Compiles and executes Lua code, saving each attempt to the session directory.
    Supports multiple sandbox modes: lua (default), docker, or none.
    """

    def __init__(
        self,
        session_dir: str | Path,
        timeout: int = 10,
        sandbox: SandboxMode = "lua",
    ):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.sandbox = sandbox
        self._check_lua_installed()
        self._docker_runner = None

        if sandbox == "docker":
            self._init_docker_runner()

    def _init_docker_runner(self) -> None:
        """Initialize Docker runner if docker mode is enabled."""
        try:
            from tools.docker_sandbox import DockerLuaRunner, DockerConfig
            config = DockerConfig(timeout=self.timeout)
            self._docker_runner = DockerLuaRunner(self.session_dir, config)
        except ImportError as e:
            raise ImportError(
                f"Docker sandbox requires docker_sandbox module: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Docker sandbox: {e}\n"
                "Make sure Docker is installed and running."
            )

    def _check_lua_installed(self) -> None:
        if not shutil.which("lua") and not shutil.which("lua5.4") and not shutil.which("lua5.3"):
            raise EnvironmentError(
                "Lua interpreter not found. Install it with: apt install lua5.4 / brew install lua"
            )

    def _get_lua_binary(self) -> str:
        for name in ("lua", "lua5.4", "lua5.3"):
            if shutil.which(name):
                return name
        raise EnvironmentError("No Lua binary found")

    def save_iteration(self, code: str, iteration: int) -> Path:
        """Save code to workspace as iteration_N.lua"""
        path = self.session_dir / f"iteration_{iteration}.lua"
        path.write_text(code, encoding="utf-8")
        return path

    def compile(self, code: str, iteration: int) -> LuaResult:
        """Run luac syntax check. No execution."""
        lua_file = self.save_iteration(code, iteration)

        if not shutil.which("luac"):
            # Fallback: use lua -l (load only) if luac not available
            return self._compile_with_lua(lua_file)

        result = subprocess.run(
            ["luac", "-o", _NULL_DEVICE, str(lua_file)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return LuaResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def _compile_with_lua_check(self, lua_file: Path) -> LuaResult:
        """Compile via lua --syntax check fallback."""
        result = subprocess.run(
            [self._get_lua_binary(), "-", str(lua_file)],
            input=f'local ok, err = loadfile("{lua_file}") if not ok then io.stderr:write(err) os.exit(1) end',
            capture_output=True,
            text=True,
            timeout=5,
        )
        return LuaResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def _compile_with_lua(self, lua_file: Path) -> LuaResult:
        check_script = f'local ok, err = loadfile("{lua_file}") if not ok then io.stderr:write(err) os.exit(1) end'
        result = subprocess.run(
            [self._get_lua_binary()],
            input=check_script,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return LuaResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def execute(self, code: str, iteration: int) -> LuaResult:
        """Compile + execute Lua code with timeout. Sandbox mode configurable."""
        # Docker mode: delegate to Docker runner
        if self.sandbox == "docker":
            if self._docker_runner is None:
                raise RuntimeError("Docker runner not initialized")
            return self._docker_runner.execute(code, iteration)

        # Lua/none mode: local execution
        lua_file = self.save_iteration(code, iteration)

        # Step 1: compile (original code, no sandbox — sandbox preamble is valid Lua)
        compile_result = self.compile(code, iteration)
        if not compile_result.success:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(compile_result.errors, encoding="utf-8")
            return compile_result

        # Step 2: wrap in sandbox and execute (if sandbox enabled)
        if self.sandbox == "lua":
            exec_code = wrap_in_sandbox(code)
            exec_file = self.session_dir / f"iteration_{iteration}_sandboxed.lua"
            exec_file.write_text(exec_code, encoding="utf-8")
        else:
            # No sandbox mode
            exec_file = lua_file

        # Step 3: Add profiling wrapper
        profiled_code = self._wrap_with_profiling(exec_file.read_text(encoding="utf-8"))
        profiled_file = self.session_dir / f"iteration_{iteration}_profiled.lua"
        profiled_file.write_text(profiled_code, encoding="utf-8")

        try:
            import time
            start_time = time.perf_counter()

            result = subprocess.run(
                [self._get_lua_binary(), str(profiled_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            execution_time = time.perf_counter() - start_time

            # Parse profiling output from stderr (where it's written)
            memory_used = self._parse_memory_from_output(result.stderr)

            lua_result = LuaResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                compiled_ok=True,  # syntax was valid
                execution_time=execution_time,
                memory_used=memory_used,
            )
        except subprocess.TimeoutExpired:
            lua_result = LuaResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.timeout}s",
                timed_out=True,
                compiled_ok=True,
            )

        # Intentional errors (e.g. error("Division by zero")) are not real failures
        if lua_result.is_intentional_error:
            lua_result.success = True

        # Save errors only for real failures
        if not lua_result.success:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(lua_result.errors, encoding="utf-8")

        return lua_result

    def _wrap_with_profiling(self, code: str) -> str:
        """Wrap code with profiling instrumentation."""
        # Check if code ends with a return statement
        lines = code.rstrip().split('\n')
        has_trailing_return = False
        return_statement = ""

        # Find trailing return (ignoring comments and empty lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if not line or line.startswith('--'):
                continue
            if line.startswith('return '):
                has_trailing_return = True
                return_statement = lines[i]
                lines = lines[:i]  # Remove return from code
                break
            else:
                break

        code_without_return = '\n'.join(lines)

        # Build profiled code: start profiling -> code -> end profiling -> return
        profiling_wrapper = '''
-- ═══ Profiling Start ═══
local _start_time = os.clock()
collectgarbage("collect")
local _mem_before = collectgarbage("count")

-- ═══ User Code ═══
''' + code_without_return + '''

-- ═══ Profiling End ═══
collectgarbage("collect")
local _mem_after = collectgarbage("count")
local _elapsed = os.clock() - _start_time
local _mem_used = _mem_after - _mem_before

io.stderr:write(string.format("\\n[PROFILE] time=%.6f memory=%.2f\\n", _elapsed, _mem_used))
'''

        # Add return at the very end if it existed
        if has_trailing_return:
            profiling_wrapper += '\n' + return_statement + '\n'

        return profiling_wrapper

    def _parse_memory_from_output(self, output: str) -> int:
        """Parse memory usage from profiling output."""
        import re
        match = re.search(r'\[PROFILE\].*memory=([\d.]+)', output)
        if match:
            return int(float(match.group(1)))
        return 0
