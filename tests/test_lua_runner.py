"""
LuaRunner tests — require lua to be installed.
Tests marked with @pytest.mark.skipif if lua not available.
"""
import pytest
import shutil
import tempfile
import os
from pathlib import Path
from tools.lua_runner import LuaRunner, LuaResult

LUA_AVAILABLE = bool(shutil.which("lua") or shutil.which("lua5.4") or shutil.which("lua5.3"))


@pytest.fixture
def runner():
    with tempfile.TemporaryDirectory() as d:
        yield LuaRunner(session_dir=d, timeout=5)


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_valid_lua_compiles(runner):
    result = runner.compile('print("hello")', iteration=1)
    assert result.success


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_invalid_lua_fails_compile(runner):
    result = runner.compile("local x = (((", iteration=1)
    assert not result.success
    assert result.errors


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_execute_returns_stdout(runner):
    result = runner.execute('io.write("42")', iteration=1)
    assert result.success
    assert "42" in result.stdout


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_execute_runtime_error(runner):
    result = runner.execute('error("boom")', iteration=1)
    assert not result.success
    assert result.errors


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_iteration_files_saved(runner):
    runner.execute('print("ok")', iteration=3)
    session_files = list(Path(runner.session_dir).iterdir())
    names = [f.name for f in session_files]
    assert "iteration_3.lua" in names


@pytest.mark.skipif(not LUA_AVAILABLE, reason="lua not installed")
def test_error_file_saved_on_failure(runner):
    runner.execute("invalid lua !!!", iteration=2)
    session_files = list(Path(runner.session_dir).iterdir())
    names = [f.name for f in session_files]
    assert "iteration_2_errors.txt" in names


def test_lua_result_str_ok():
    r = LuaResult(success=True, stdout="hello", stderr="")
    assert "OK" in str(r)


def test_lua_result_str_error():
    r = LuaResult(success=False, stdout="", stderr="syntax error")
    assert "ERROR" in str(r)


def test_lua_result_str_timeout():
    r = LuaResult(success=False, stdout="", stderr="timed out", timed_out=True)
    assert "TIMEOUT" in str(r)
