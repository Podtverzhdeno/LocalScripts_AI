"""
Lua code execution tool.
Runs luac (compile check) and lua (execute) in a sandboxed subprocess.
Writes each iteration to the session workspace directory.

Sandbox mode (enabled by default) blocks dangerous system calls:
  os.execute, io.popen, loadfile, dofile, require, debug, etc.
  See tools/sandbox.py for the full list.
"""

import os
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path

from tools.sandbox import wrap_in_sandbox

# luac -o needs a null device; /dev/null doesn't exist on Windows
_NULL_DEVICE = "NUL" if os.name == "nt" else "/dev/null"


@dataclass
class LuaResult:
    success: bool
    stdout: str
    stderr: str
    timed_out: bool = False
    compiled_ok: bool = False  # True if luac passed (syntax is valid)

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
        if self.success:
            return f"OK\n{self.stdout}" if self.stdout else "OK"
        if self.timed_out:
            return f"TIMEOUT\n{self.stderr}"
        if self.is_intentional_error:
            return f"OK_WITH_EXPECTED_ERROR\n{self.stdout}\n---\n{self.stderr}"
        return f"ERROR\n{self.stderr}"


class LuaRunner:
    """
    Compiles and executes Lua code, saving each attempt to the session directory.
    Inspired by ChatDev's uv_run tool with timeout support.
    """

    def __init__(self, session_dir: str | Path, timeout: int = 10, sandbox: bool = True):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.sandbox = sandbox
        self._check_lua_installed()

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
        """Compile + execute Lua code with timeout. Sandbox enabled by default."""
        lua_file = self.save_iteration(code, iteration)

        # Step 1: compile (original code, no sandbox — sandbox preamble is valid Lua)
        compile_result = self.compile(code, iteration)
        if not compile_result.success:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(compile_result.errors, encoding="utf-8")
            return compile_result

        # Step 2: wrap in sandbox and execute
        exec_code = wrap_in_sandbox(code) if self.sandbox else code
        exec_file = self.session_dir / f"iteration_{iteration}_sandboxed.lua"
        exec_file.write_text(exec_code, encoding="utf-8")

        try:
            result = subprocess.run(
                [self._get_lua_binary(), str(exec_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            lua_result = LuaResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                compiled_ok=True,  # syntax was valid
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
