-- Define a simple calculator with basic arithmetic operations

local function create_calculator()
    local calc = {}

    -- Addition
    calc.add = load([[
        return x + y
    ]])

    -- Subtraction
    calc.sub = load([[
        return x - y
    ]])

    -- Multiplication
    calc.mul = load([[
        return x * y
    ]])

    -- Division
    calc.div = load([[
        if y == 0 then error("Division by zero") end
        return x / y
    ]])

    return calc
end

-- Example usage:
local calculator = create_calculator()
print(calculator.add(5, 3))       -- Output: 8
print(calculator.sub(10, 4))     -- Output: 6
print(calculator.mul(7, 2))      -- Output: 14
print(calculator.div(9, 3))      -- Output: 3

-- Test division by zero error
pcall(function() print(calculator.div(8, 0)) end) -- Should raise an error