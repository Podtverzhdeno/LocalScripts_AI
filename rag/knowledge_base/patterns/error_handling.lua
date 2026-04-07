-- Error Handling Strategies Pattern
-- Comprehensive error handling patterns for robust applications
-- Use case: Production systems, fault tolerance, debugging

-- Result type (success/error wrapper)
local Result = {}
Result.__index = Result

function Result.ok(value)
    return setmetatable({
        success = true,
        value = value
    }, Result)
end

function Result.err(error)
    return setmetatable({
        success = false,
        error = error
    }, Result)
end

function Result:is_ok()
    return self.success
end

function Result:is_err()
    return not self.success
end

function Result:unwrap()
    if self.success then
        return self.value
    else
        error("Called unwrap on error result: " .. tostring(self.error))
    end
end

function Result:unwrap_or(default)
    if self.success then
        return self.value
    else
        return default
    end
end

function Result:map(func)
    if self.success then
        return Result.ok(func(self.value))
    else
        return self
    end
end

-- Try-catch-finally pattern
function try(try_func, catch_func, finally_func)
    local success, result = pcall(try_func)

    if not success and catch_func then
        result = catch_func(result)
    end

    if finally_func then
        finally_func()
    end

    return success, result
end

-- Error with context
local function create_error(message, context)
    return {
        message = message,
        context = context or {},
        timestamp = os.time(),
        stack = debug.traceback()
    }
end

-- Safe function wrapper
function safe(func)
    return function(...)
        local success, result = pcall(func, ...)
        if success then
            return Result.ok(result)
        else
            return Result.err(result)
        end
    end
end

-- Validation with multiple errors
local Validator = {}
Validator.__index = Validator

function Validator.new()
    local self = setmetatable({}, Validator)
    self.errors = {}
    return self
end

function Validator:add_error(field, message)
    if not self.errors[field] then
        self.errors[field] = {}
    end
    table.insert(self.errors[field], message)
end

function Validator:is_valid()
    return next(self.errors) == nil
end

function Validator:get_errors()
    return self.errors
end

function Validator:validate(field, value, rules)
    for _, rule in ipairs(rules) do
        if not rule.check(value) then
            self:add_error(field, rule.message)
        end
    end
end

-- Common validation rules
local Rules = {
    required = function(message)
        return {
            check = function(value)
                return value ~= nil and value ~= ""
            end,
            message = message or "Field is required"
        }
    end,

    min_length = function(min, message)
        return {
            check = function(value)
                return type(value) == "string" and #value >= min
            end,
            message = message or string.format("Minimum length is %d", min)
        }
    end,

    email = function(message)
        return {
            check = function(value)
                return type(value) == "string" and value:match("^[%w%._%+%-]+@[%w%.%-]+%.%w+$")
            end,
            message = message or "Invalid email format"
        }
    end
}

-- Example usage:
-- Using Result type
-- local function divide(a, b)
--     if b == 0 then
--         return Result.err("Division by zero")
--     end
--     return Result.ok(a / b)
-- end
--
-- local result = divide(10, 2)
-- if result:is_ok() then
--     print("Result:", result:unwrap())
-- else
--     print("Error:", result.error)
-- end
--
-- Using Validator
-- local validator = Validator.new()
-- validator:validate("email", "invalid", {Rules.required(), Rules.email()})
-- validator:validate("password", "123", {Rules.required(), Rules.min_length(8)})
--
-- if validator:is_valid() then
--     print("Valid!")
-- else
--     for field, errors in pairs(validator:get_errors()) do
--         print(field .. ":", table.concat(errors, ", "))
--     end
-- end
