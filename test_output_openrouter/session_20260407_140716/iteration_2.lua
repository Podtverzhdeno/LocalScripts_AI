-- Factorial function with input validation
local function factorial(n)
    n = math.max(0, math.floor(n)) -- Ensure n is a non-negative integer
    if n == 0 then return 1 end
    
    local result = 1
    for i = 1, n do
        result = result * i
    end
    return result
end

-- Example usage
local test_values = {5, 0, -3, 3.7, 4}
for _, value in ipairs(test_values) do
    local ok, result = pcall(factorial, value)
    if ok then
        print("Factorial of " .. value .. " is " .. result)
    else
        print("Error calculating factorial of " .. value .. ": " .. result)
    end
end