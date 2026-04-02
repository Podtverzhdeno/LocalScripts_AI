```lua
-- Simple calculator in Lua

function calculate(expression)
    -- Load and evaluate the expression safely
    local func = loadstring("return " .. expression)
    
    if not func then
        return "Invalid expression"
    end
    
    -- Evaluate the function
    local result = pcall(func)
    
    if result then
        return func()
    else
        return "Error evaluating expression"
    end
end

-- Example usage:
print(calculate("2 + 3 * 4"))  -- Should print 14
print(calculate("(2 + 3) * 4"))  -- Should print 20
print(calculate("2 +"))  -- Should return "Invalid expression"
```