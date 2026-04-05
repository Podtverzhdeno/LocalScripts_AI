"""
Sandbox tests — verify that dangerous Lua functions are blocked.
Requires lua to be installed.
"""
import pytest
import shutil
import tempfile
from tools.lua_runner import LuaRunner, LuaResult
from tools.sandbox import wrap_in_sandbox, BLOCKED_FUNCTIONS, SAFE_FUNCTIONS

LUA_AVAILABLE = bool(shutil.which("lua") or shutil.which("lua5.4") or shutil.which("lua5.3"))


@pytest.fixture
def runner():
    """Runner with sandbox enabled (default)."""
    with tempfile.TemporaryDirectory() as d:
        yield LuaRunner(session_dir=d, timeout=5, sandbox=True)


@pytest.fixture
def unsafe_runner():
    """Runner with sandbox disabled — for comparison tests."""
    with tempfile.TemporaryDirectory() as d:
        yield LuaRunner(session_dir=d, timeout=5, sandbox=False)


# --- Sandbox blocks dangerous calls ---

@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_os_execute(runner):
    result = runner.execute('os.execute("echo pwned")', iteration=1)
    assert not result.success
    assert "SANDBOX" in result.errors or "blocked" in result.errors.lower()


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_os_remove(runner):
    result = runner.execute('os.remove("/tmp/test")', iteration=1)
    assert not result.success
    assert "SANDBOX" in result.errors


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_os_exit(runner):
    result = runner.execute('os.exit(1)', iteration=1)
    assert not result.success
    assert "SANDBOX" in result.errors


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_require(runner):
    result = runner.execute('local json = require("json")', iteration=1)
    assert not result.success
    # require is nil, so Lua gives "attempt to call a nil value"
    assert "nil" in result.errors.lower() or "SANDBOX" in result.errors


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_loadfile(runner):
    result = runner.execute('loadfile("/etc/passwd")', iteration=1)
    assert not result.success


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_dofile(runner):
    result = runner.execute('dofile("/etc/passwd")', iteration=1)
    assert not result.success


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_debug(runner):
    result = runner.execute('print(debug.getinfo(1))', iteration=1)
    assert not result.success


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_io_popen(runner):
    """io.popen is removed — io table only has read/write/stdout/stderr."""
    result = runner.execute('io.popen("ls")', iteration=1)
    assert not result.success


# --- Sandbox preserves safe functions ---

@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_print(runner):
    result = runner.execute('print("hello sandbox")', iteration=1)
    assert result.success
    assert "hello sandbox" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_math(runner):
    result = runner.execute('print(math.sqrt(144))', iteration=1)
    assert result.success
    assert "12" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_string(runner):
    result = runner.execute('print(string.upper("hello"))', iteration=1)
    assert result.success
    assert "HELLO" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_table(runner):
    result = runner.execute(
        'local t = {3,1,2}; table.sort(t); print(table.concat(t, ","))',
        iteration=1,
    )
    assert result.success
    assert "1,2,3" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_os_clock(runner):
    result = runner.execute('print(type(os.clock()))', iteration=1)
    assert result.success
    assert "number" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_pcall(runner):
    result = runner.execute(
        'local ok, err = pcall(function() error("test") end)\n'
        'print(ok, err)',
        iteration=1,
    )
    assert result.success
    assert "false" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_coroutine(runner):
    code = '''
local co = coroutine.create(function() coroutine.yield(42) end)
local ok, val = coroutine.resume(co)
print(val)
'''
    result = runner.execute(code, iteration=1)
    assert result.success
    assert "42" in result.stdout


# --- Sandbox can be disabled ---

@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_no_sandbox_allows_os_execute(unsafe_runner):
    """With sandbox=False, os.execute should work."""
    result = unsafe_runner.execute('print(os.execute("echo ok"))', iteration=1)
    # os.execute returns true/nil + exit status — just check it doesn't error with SANDBOX
    assert "SANDBOX" not in (result.stderr or "")


# --- Unit tests for wrap_in_sandbox ---

def test_wrap_adds_preamble():
    code = 'print("hello")'
    wrapped = wrap_in_sandbox(code)
    assert "LocalScript Sandbox" in wrapped
    assert code in wrapped
    assert wrapped.endswith(code)


def test_wrap_preserves_original_code():
    code = 'local x = 1\nprint(x)'
    wrapped = wrap_in_sandbox(code)
    assert code in wrapped
