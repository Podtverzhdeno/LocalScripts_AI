
-- ═══ Profiling Start ═══
local _start_time = os.clock()
collectgarbage("collect")
local _mem_before = collectgarbage("count")

-- ═══ User Code ═══
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

-- Function to calculate the factorial of a non-negative integer
local function factorial(n)
    -- Check if n is a non-negative integer
    if type(n) ~= "number" or n < 0 or n % 1 ~= 0 then
        return nil, "Input must be a non-negative integer"
    end

    local result = 1
    for i = 2, n do
        result = result * i
    end
    return result
end

-- Example usage and error handling
local inputs = {5, 0, -3, 3.5, "text"}
for _, input in ipairs(inputs) do
    local ok, result = pcall(factorial, input)
    if not ok then
        print("Caught error: " .. result)
    else
        if result then
            print("Factorial of " .. input .. " is " .. result)
        else
            print("Error for input " .. input .. ": " .. result)
        end
    end
end

-- ═══ Profiling End ═══
collectgarbage("collect")
local _mem_after = collectgarbage("count")
local _elapsed = os.clock() - _start_time
local _mem_used = _mem_after - _mem_before

io.stderr:write(string.format("\n[PROFILE] time=%.6f memory=%.2f\n", _elapsed, _mem_used))
