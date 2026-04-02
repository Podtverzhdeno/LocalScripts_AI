```lua
-- Simple calculator in Lua

function calculate(expression)
    -- Load and evaluate the arithmetic expression
    local result = loadstring("return " .. expression)()
    
    -- Return the result of the calculation
    return result
end

-- Test cases
print(calculate("2 + 3"))       -- Output: 5
print(calculate("10 - 4 * 2"))  -- Output: 2
print(calculate("(7 / 3) ^ 2")) -- Output: 5.166666666666667
```