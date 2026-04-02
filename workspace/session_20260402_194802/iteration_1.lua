-- Lua Calculator

local function calc(expr)
    local tokens = {}
    for token in string.gmatch(expr, "%S+") do
        table.insert(tokens, token)
    end
    
    local stack = {}
    for _, token in ipairs(tokens) do
        if tonumber(token) then
            table.insert(stack, tonumber(token))
        else
            local b = table.remove(stack)
            local a = table.remove(stack)
            local res
            if token == "+" then
                res = a + b
            elseif token == "-" then
                res = a - b
            elseif token == "*" then
                res = a * b
            elseif token == "/" then
                res = a / b
            end
            table.insert(stack, res)
        end
    end
    
    return stack[1]
end

print(calc("3 4 +")) -- 7
print(calc("5 2 -")) -- 3
print(calc("6 3 *")) -- 18
print(calc("9 3 /")) -- 3