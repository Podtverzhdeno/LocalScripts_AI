"""
Lua code execution tool.
Runs luac (compile check) and lua (execute) in a sandboxed subprocess.
Writes each iteration to the session workspace directory.
"""

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LuaResult:
    success: bool
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def errors(self) -> str:
        """Return combined error output."""
        return self.stderr.strip()

    def __str__(self) -> str:
        if self.success:
            return f"OK\n{self.stdout}" if self.stdout else "OK"
        if self.timed_out:
            return f"TIMEOUT\n{self.stderr}"
        return f"ERROR\n{self.stderr}"


class LuaRunner:
    """
    Compiles and executes Lua code, saving each attempt to the session directory.
    Inspired by ChatDev's uv_run tool with timeout support.
    """

    def __init__(self, session_dir: str | Path, timeout: int = 10):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
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
            ["luac", "-o", "/dev/null", str(lua_file)],
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
        """Compile + execute Lua code with timeout."""
        lua_file = self.save_iteration(code, iteration)

        # Step 1: compile
        compile_result = self.compile(code, iteration)
        if not compile_result.success:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(compile_result.errors, encoding="utf-8")
            return compile_result

        # Step 2: execute
        try:
            result = subprocess.run(
                [self._get_lua_binary(), str(lua_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            lua_result = LuaResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            lua_result = LuaResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.timeout}s",
                timed_out=True,
            )

        # Save errors if any
        if not lua_result.success:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(lua_result.errors, encoding="utf-8")

        return lua_result
