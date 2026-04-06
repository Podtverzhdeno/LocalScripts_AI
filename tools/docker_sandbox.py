"""
Docker-based sandbox for Lua code execution.
Provides full isolation by running code in a disposable container.

Usage:
    runner = DockerLuaRunner(session_dir="./workspace/session_123")
    result = runner.execute(code, iteration=1)

Requirements:
    - Docker installed and running
    - Dockerfile.sandbox in project root
"""

import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass

from tools.lua_runner import LuaResult


@dataclass
class DockerConfig:
    """Docker sandbox configuration."""
    image_name: str = "localscript-lua-sandbox"
    memory_limit: str = "128m"
    cpu_quota: int = 50000  # 50% of one CPU
    network: str = "none"  # No network access
    timeout: int = 10


class DockerLuaRunner:
    """
    Executes Lua code in an isolated Docker container.
    Each execution runs in a fresh container that is destroyed after completion.
    """

    def __init__(self, session_dir: str | Path, config: DockerConfig | None = None):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or DockerConfig()
        self._check_docker_available()
        self._ensure_image_built()

    def _check_docker_available(self) -> None:
        """Check if Docker is installed and running."""
        if not shutil.which("docker"):
            raise EnvironmentError(
                "Docker not found. Install Docker Desktop or Docker Engine."
            )

        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise EnvironmentError("Docker daemon is not running. Start Docker and retry.")
        except subprocess.TimeoutExpired:
            raise EnvironmentError("Docker daemon is not responding.")

    def _ensure_image_built(self) -> None:
        """Build Docker image if it doesn't exist."""
        result = subprocess.run(
            ["docker", "images", "-q", self.config.image_name],
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print(f"Building Docker image {self.config.image_name}...")
            self._build_image()

    def _build_image(self) -> None:
        """Build the sandbox Docker image."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile.sandbox"

        if not dockerfile_path.exists():
            raise FileNotFoundError(
                f"Dockerfile.sandbox not found at {dockerfile_path}. "
                "Create it with: make docker-sandbox-build"
            )

        result = subprocess.run(
            [
                "docker", "build",
                "-f", str(dockerfile_path),
                "-t", self.config.image_name,
                str(dockerfile_path.parent),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to build Docker image:\n{result.stderr}")

    def save_iteration(self, code: str, iteration: int) -> Path:
        """Save code to workspace as iteration_N.lua"""
        path = self.session_dir / f"iteration_{iteration}.lua"
        path.write_text(code, encoding="utf-8")
        return path

    def execute(self, code: str, iteration: int) -> LuaResult:
        """
        Execute Lua code in an isolated Docker container.

        Security features:
        - No network access
        - Limited memory and CPU
        - Read-only filesystem (except /tmp)
        - No privileged operations
        - Container destroyed after execution
        """
        lua_file = self.save_iteration(code, iteration)

        try:
            result = subprocess.run(
                [
                    "docker", "run",
                    "--rm",  # Remove container after execution
                    "--network", self.config.network,
                    "--memory", self.config.memory_limit,
                    "--cpu-quota", str(self.config.cpu_quota),
                    "--read-only",  # Read-only root filesystem
                    "--tmpfs", "/tmp:rw,noexec,nosuid,size=10m",  # Small writable tmp
                    "--security-opt", "no-new-privileges",
                    "-v", f"{lua_file.absolute()}:/code.lua:ro",  # Mount code read-only
                    self.config.image_name,
                    "lua", "/code.lua",
                ],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )

            lua_result = LuaResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                compiled_ok=True,
            )

        except subprocess.TimeoutExpired:
            lua_result = LuaResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {self.config.timeout}s",
                timed_out=True,
                compiled_ok=True,
            )
        except Exception as e:
            lua_result = LuaResult(
                success=False,
                stdout="",
                stderr=f"Docker execution failed: {str(e)}",
                compiled_ok=False,
            )

        # Save errors for real failures
        if not lua_result.success and not lua_result.is_intentional_error:
            err_path = self.session_dir / f"iteration_{iteration}_errors.txt"
            err_path.write_text(lua_result.errors, encoding="utf-8")

        return lua_result
