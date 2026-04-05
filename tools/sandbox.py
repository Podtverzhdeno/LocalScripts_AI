"""
Lua sandbox — restricts dangerous system calls before code execution.

Wraps user code in a safe environment that blocks:
  - os.execute, os.remove, os.rename, os.tmpname
  - io.popen, io.open (write mode)
  - loadfile, dofile (arbitrary file execution)
  - debug library (full introspection bypass)
  - rawset on _G (global table pollution)
  - require (external modules — already banned by prompt, enforced here)

Safe functions are preserved:
  - print, type, tostring, tonumber, error, assert, pcall, xpcall
  - string.*, table.*, math.*, coroutine.*, utf8.*
  - os.clock, os.date, os.time, os.difftime
  - io.read, io.write, io.stdout, io.stderr (read + stdout only)
  - pairs, ipairs, next, select, unpack, rawget, rawlen, rawequal
"""

# Lua sandbox preamble — injected before user code.
# Uses Lua 5.3+ syntax. Blocks dangerous functions by setting them to nil
# or replacing with error-throwing stubs.
_SANDBOX_PREAMBLE = '''\
-- ══ LocalScript Sandbox ══
-- Blocks dangerous system calls for safe code execution.
local _original_print = print
local _original_error = error

-- Block dangerous os functions (keep safe ones)
local _safe_os = {
    clock = os.clock,
    date = os.date,
    time = os.time,
    difftime = os.difftime,
}
os = _safe_os

-- Block dangerous io functions (keep stdout/stderr/read)
local _safe_io = {
    read = io.read,
    write = io.write,
    stdout = io.stdout,
    stderr = io.stderr,
}
io = _safe_io

-- Block file/module loading
loadfile = nil
dofile = nil
require = nil
package = nil

-- Block debug library entirely
debug = nil

-- Block raw global table manipulation
rawset = nil

-- Stub for blocked functions — clear error message
local function _blocked(name)
    return function()
        _original_error(
            "[SANDBOX] " .. name .. " is blocked for security. "
            .. "Only standard Lua built-in functions are allowed.",
            2
        )
    end
end

-- Ensure commonly attempted dangerous calls give clear errors
os.execute = _blocked("os.execute")
os.remove = _blocked("os.remove")
os.rename = _blocked("os.rename")
os.exit = _blocked("os.exit")
os.getenv = _blocked("os.getenv")
os.tmpname = _blocked("os.tmpname")

-- ══ End Sandbox — user code below ══

'''

# Functions that the sandbox blocks — used for validation/testing
BLOCKED_FUNCTIONS = frozenset({
    "os.execute", "os.remove", "os.rename", "os.exit",
    "os.getenv", "os.tmpname",
    "io.popen", "io.open",
    "loadfile", "dofile", "require",
    "debug.getinfo", "debug.sethook",
})

# Functions that remain available
SAFE_FUNCTIONS = frozenset({
    "print", "type", "tostring", "tonumber", "error", "assert",
    "pcall", "xpcall", "pairs", "ipairs", "next", "select",
    "unpack", "rawget", "rawlen", "rawequal",
    "string.format", "string.find", "string.gsub",
    "table.insert", "table.remove", "table.sort", "table.concat",
    "math.floor", "math.ceil", "math.random", "math.sqrt",
    "os.clock", "os.date", "os.time",
    "io.read", "io.write",
})


def wrap_in_sandbox(code: str) -> str:
    """Wrap Lua code in a sandbox that blocks dangerous system calls."""
    return _SANDBOX_PREAMBLE + code
