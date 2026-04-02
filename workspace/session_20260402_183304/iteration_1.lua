-- Define a simple calculator function
local function calculator(expression)
    -- Use loadstring to evaluate the expression safely
    local func, err = loadstring("return " .. expression)
    if not func then return nil, err end
    
    -- Evaluate and return the result
    local result = pcall(func)
    if result then
        return func()
    else
        return nil, debug.getmsg()
    end
end

-- Test cases to demonstrate functionality
print(calculator("2 + 3"))       -- Output: 5
print(calculator("10 * 5"))     -- Output: 50
print(calculator("(4 + 6) / 2"))-- Output: 5
print(calculator("invalid expr"))-- Output: nil, error message