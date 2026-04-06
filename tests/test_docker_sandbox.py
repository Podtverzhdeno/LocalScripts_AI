"""
Docker sandbox tests — require Docker to be installed and running.
Tests marked with @pytest.mark.skipif if Docker not available.
"""
import pytest
import shutil
import tempfile
import subprocess
from pathlib import Path
from tools.docker_sandbox import DockerLuaRunner, DockerConfig

DOCKER_AVAILABLE = bool(shutil.which("docker"))


def is_docker_running():
    """Check if Docker daemon is running."""
    if not DOCKER_AVAILABLE:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except:
        return False


def is_docker_image_built():
    """Check if sandbox image is built."""
    if not is_docker_running():
        return False
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "localscript-lua-sandbox"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(result.stdout.strip())
    except:
        return False


DOCKER_IMAGE_AVAILABLE = is_docker_image_built()


@pytest.fixture
def docker_runner():
    if not DOCKER_IMAGE_AVAILABLE:
        pytest.skip("Docker image not built. Run: make docker-sandbox-build")
    with tempfile.TemporaryDirectory() as d:
        config = DockerConfig(timeout=5)
        yield DockerLuaRunner(session_dir=d, config=config)


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_runner_initialization(docker_runner):
    """Verify Docker runner initializes correctly."""
    assert docker_runner.session_dir.exists()
    assert docker_runner.config.image_name == "localscript-lua-sandbox"


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_executes_valid_code(docker_runner):
    """Verify Docker runner executes valid Lua code."""
    code = 'print("hello from docker")'
    result = docker_runner.execute(code, iteration=1)
    assert result.success
    assert "hello from docker" in result.stdout


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_blocks_os_execute(docker_runner):
    """Verify os.execute fails in Docker (no shell access)."""
    code = 'os.execute("echo hacked")'
    result = docker_runner.execute(code, iteration=1)
    # Should fail because os.execute is not available in minimal Alpine
    assert not result.success or result.stdout == ""


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_timeout(docker_runner):
    """Verify Docker execution respects timeout."""
    code = 'while true do end'  # Infinite loop
    result = docker_runner.execute(code, iteration=1)
    assert not result.success
    assert result.timed_out
    assert "timed out" in result.stderr.lower()


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_saves_iteration_files(docker_runner):
    """Verify iteration files are saved."""
    code = 'print("test")'
    docker_runner.execute(code, iteration=3)
    session_files = list(Path(docker_runner.session_dir).iterdir())
    names = [f.name for f in session_files]
    assert "iteration_3.lua" in names


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_handles_syntax_errors(docker_runner):
    """Verify Docker runner handles syntax errors."""
    code = 'local x = ((('
    result = docker_runner.execute(code, iteration=1)
    assert not result.success
    assert result.stderr


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_handles_runtime_errors(docker_runner):
    """Verify Docker runner handles runtime errors."""
    code = 'error("boom")'
    result = docker_runner.execute(code, iteration=1)
    assert not result.success
    assert "boom" in result.stderr


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_allows_safe_operations(docker_runner):
    """Verify safe Lua operations work in Docker."""
    code = '''
    local t = {1, 2, 3}
    for i, v in ipairs(t) do
        print(v * 2)
    end
    print(math.sqrt(16))
    print(string.upper("test"))
    '''
    result = docker_runner.execute(code, iteration=1)
    assert result.success
    assert "2" in result.stdout
    assert "4" in result.stdout
    assert "6" in result.stdout
    assert "TEST" in result.stdout


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_no_network_access(docker_runner):
    """Verify Docker container has no network access."""
    # This test assumes the container has no network tools
    # In minimal Alpine with only Lua, there's no way to test network
    # But we verify the config is set correctly
    assert docker_runner.config.network == "none"


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_memory_limit(docker_runner):
    """Verify Docker container has memory limit."""
    assert docker_runner.config.memory_limit == "128m"


@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="docker not installed")
def test_docker_cpu_limit(docker_runner):
    """Verify Docker container has CPU limit."""
    assert docker_runner.config.cpu_quota == 50000  # 50% of one CPU
