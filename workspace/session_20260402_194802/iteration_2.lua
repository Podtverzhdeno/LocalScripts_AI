-- This function calculates arithmetic expressions provided as space-separated tokens
local function calculate(expression)
    local tokens = {}
    -- Split input into tokens based on spaces
    for token in string.gmatch(expression, "%S+") do
        table.insert(tokens, token)
    end
    
    local stack = {}
    -- Process each token
    for _, token in ipairs(tokens) do
        if tonumber(token) then
            -- Push numbers onto the stack
            table.insert(stack, tonumber(token))
        else
            -- Pop two values from the stack and perform operation
            local b = table.remove(stack)
            local a = table.remove(stack)
            local result
            if token == "+" then
                result = a + b
            elseif token == "-" then
                result = a - b
            elseif token == "*" then
                result = a * b
            elseif token == "/" and b ~= 0 then
                -- Handle division by zero error
                result = a / b
            else
                error("Invalid operation or division by zero")
            end
            table.insert(stack, result)
        end
    end
    
    return stack[1]
end

-- Test cases to demonstrate functionality
print(calculate("3 4 +")) -- 7
print(calculate("5 2 -")) -- 3
print(calculate("6 3 *")) -- 18
print(calculate("9 0 /")) -- Error: Invalid operation or division by zero