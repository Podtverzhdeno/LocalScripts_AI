"""
Enhanced sandbox tests — verify metatable protection and bypass prevention.
"""
import pytest
import shutil
import tempfile
from pathlib import Path
from tools.lua_runner import LuaRunner

LUA_AVAILABLE = bool(shutil.which("lua") or shutil.which("lua5.4") or shutil.which("lua5.3"))


@pytest.fixture
def runner():
    with tempfile.TemporaryDirectory() as d:
        yield LuaRunner(session_dir=d, timeout=5, sandbox="lua")


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_os_execute(runner):
    """Verify os.execute is blocked."""
    code = 'os.execute("echo hacked")'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr
    assert "os.execute" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_io_popen(runner):
    """Verify io.popen is blocked."""
    code = 'io.popen("ls")'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr or "nil" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_loadfile(runner):
    """Verify loadfile is blocked."""
    code = 'loadfile("/etc/passwd")'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "nil" in result.stderr or "attempt to call" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_require(runner):
    """Verify require is blocked."""
    code = 'require("os")'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "nil" in result.stderr or "attempt to call" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_debug(runner):
    """Verify debug library is blocked."""
    code = 'debug.getinfo(1)'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "nil" in result.stderr or "attempt to index" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_rawset(runner):
    """Verify rawset is blocked."""
    code = 'rawset(_G, "os", {})'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "nil" in result.stderr or "attempt to call" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_blocks_load(runner):
    """Verify load is blocked."""
    code = 'load("os.execute(\\"echo hacked\\")")'
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_metatable_protection_os(runner):
    """Verify os table metatable is protected."""
    code = '''
    local mt = getmetatable(os)
    print(mt)
    '''
    result = runner.execute(code, iteration=1)
    # Should print nil (metatable hidden)
    assert result.success
    assert "nil" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_prevents_os_modification(runner):
    """Verify os table cannot be modified."""
    code = '''
    os.execute = function() print("bypassed") end
    '''
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr or "Cannot modify" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_prevents_io_modification(runner):
    """Verify io table cannot be modified."""
    code = '''
    io.popen = function() print("bypassed") end
    '''
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr or "Cannot modify" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_safe_os_functions(runner):
    """Verify safe os functions still work."""
    code = '''
    print(os.time())
    print(os.clock())
    print(os.date("%Y"))
    '''
    result = runner.execute(code, iteration=1)
    assert result.success
    assert result.stdout.strip()


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_safe_io_functions(runner):
    """Verify safe io functions still work."""
    code = '''
    io.write("hello")
    io.stdout:write(" world")
    '''
    result = runner.execute(code, iteration=1)
    assert result.success
    assert "hello world" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_string_table_math(runner):
    """Verify string, table, math libraries work."""
    code = '''
    print(string.upper("test"))
    print(table.concat({"a", "b"}, ","))
    print(math.sqrt(16))
    '''
    result = runner.execute(code, iteration=1)
    assert result.success
    assert "TEST" in result.stdout
    assert "a,b" in result.stdout
    assert "4" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_prevents_setmetatable_on_protected_tables(runner):
    """Verify setmetatable is restricted on protected tables."""
    code = '''
    setmetatable(os, {__index = function() return print end})
    '''
    result = runner.execute(code, iteration=1)
    assert not result.success
    assert "SANDBOX" in result.stderr or "protected" in result.stderr


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_allows_setmetatable_on_user_tables(runner):
    """Verify setmetatable works on user-created tables."""
    code = '''
    local t = {}
    setmetatable(t, {__index = function() return 42 end})
    print(t.foo)
    '''
    result = runner.execute(code, iteration=1)
    assert result.success
    assert "42" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_sandbox_prevents_dangerous_global_injection(runner):
    """Verify dangerous functions cannot be re-enabled after blocking."""
    code = '''
    -- Try to call os.execute directly (should be blocked)
    local result = pcall(function() os.execute("echo hacked") end)
    if result then
        print("bypassed")
    else
        print("blocked")
    end
    '''
    result = runner.execute(code, iteration=1)
    # Should print "blocked" because os.execute is blocked
    assert result.success
    assert "blocked" in result.stdout
