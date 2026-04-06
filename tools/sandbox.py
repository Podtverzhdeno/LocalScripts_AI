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

Enhanced security:
  - Metatable protection prevents bypassing restrictions
  - Global environment is locked after sandbox setup
"""

# Lua sandbox preamble — injected before user code.
# Uses Lua 5.3+ syntax. Blocks dangerous functions by setting them to nil
# or replacing with error-throwing stubs.
# Enhanced with metatable protection to prevent sandbox escape.
_SANDBOX_PREAMBLE = '''\
-- ══ LocalScript Sandbox (Enhanced) ══
-- Blocks dangerous system calls for safe code execution.
local _original_print = print
local _original_error = error
local _original_setmetatable = setmetatable
local _original_getmetatable = getmetatable

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

-- Block dangerous os functions (keep safe ones)
local _safe_os = {
    clock = os.clock,
    date = os.date,
    time = os.time,
    difftime = os.difftime,
}
-- Protect os table from modification
_original_setmetatable(_safe_os, {
    __index = function(t, k)
        _original_error("[SANDBOX] os." .. tostring(k) .. " is not available", 2)
    end,
    __newindex = function()
        _original_error("[SANDBOX] Cannot modify os table", 2)
    end,
    __metatable = false  -- Hide metatable
})
os = _safe_os

-- Block dangerous io functions (keep stdout/stderr/read/write)
local _safe_io = {
    read = io.read,
    write = io.write,
    stdout = io.stdout,
    stderr = io.stderr,
    type = io.type,
}
-- Protect io table from modification
_original_setmetatable(_safe_io, {
    __index = function(t, k)
        _original_error("[SANDBOX] io." .. tostring(k) .. " is not available", 2)
    end,
    __newindex = function()
        _original_error("[SANDBOX] Cannot modify io table", 2)
    end,
    __metatable = false
})
io = _safe_io

-- Block file/module loading
loadfile = nil
dofile = nil
require = nil
package = nil
load = _blocked("load")  -- Prevent loading arbitrary bytecode

-- Block debug library entirely
debug = nil

-- Block raw global table manipulation (but save rawset first for internal use)
local _internal_rawset = rawset
rawset = nil
setfenv = nil  -- Lua 5.1 compatibility
getfenv = nil  -- Lua 5.1 compatibility

-- Restrict setmetatable to prevent sandbox escape
setmetatable = function(t, mt)
    if t == _G or t == os or t == io or t == string or t == table or t == math then
        _original_error("[SANDBOX] Cannot set metatable on protected tables", 2)
    end
    return _original_setmetatable(t, mt)
end

-- Restrict getmetatable on protected tables
getmetatable = function(t)
    if t == os or t == io then
        return nil  -- Hide protected metatables
    end
    return _original_getmetatable(t)
end

-- Protect _G from modification
local _original_G_index = {}
for k, v in pairs(_G) do
    _original_G_index[k] = v
end

_original_setmetatable(_G, {
    __index = _original_G_index,
    __newindex = function(t, k, v)
        -- Allow new user-defined globals, but prevent overwriting protected ones
        if k == "os" or k == "io" or k == "debug" or k == "require" or k == "loadfile" or k == "dofile" or k == "load" then
            _original_error("[SANDBOX] Cannot modify protected global: " .. tostring(k), 2)
        end
        _internal_rawset(t, k, v)
    end,
    __metatable = false
})

-- ══ End Sandbox — user code below ══

'''

# Functions that the sandbox blocks — used for validation/testing
BLOCKED_FUNCTIONS = frozenset({
    "os.execute", "os.remove", "os.rename", "os.exit",
    "os.getenv", "os.tmpname",
    "io.popen", "io.open",
    "loadfile", "dofile", "require", "load",
    "debug.getinfo", "debug.sethook",
    "rawset", "setfenv", "getfenv",
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
