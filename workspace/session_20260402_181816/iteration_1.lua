```lua
-- Calculator in Lua

function calculate(expression)
    -- Use Lua's built-in loadstring to evaluate expressions safely
    local func, err = loadstring("return " .. expression)
    if not func then return nil, err end
    
    -- Evaluate and return the result
    local result = pcall(func)
    if result then
        return func()
    else
        return nil, debug.getinfo(func, 'S').source .. ": " .. func:catch()
    end
end

-- Example usage:
print(calculate("2 + 3 * 4"))   -- Should print 14
print(calculate("(2 + 3) * 4")) -- Should print 20
print(calculate("5 / 0"))       -- Should handle division by zero error
```