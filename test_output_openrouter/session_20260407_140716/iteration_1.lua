local function factorial(n)
    if n < 0 then
        return nil, "Factorial is not defined for negative numbers."
    elseif n == 0 then
        return 1
    else
        local result = 1
        for i = 1, n do
            result = result * i
        end
        return result
    end
end

-- Example usage
for i = 0, 5 do
    local result, err = factorial(i)
    if err then
        print("Error:", err)
    else
        print(string.format("factorial(%d) = %d", i, result))
    end
end