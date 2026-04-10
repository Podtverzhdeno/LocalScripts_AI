-- Function to calculate the factorial of a non-negative integer
local function factorial(n)
    -- Check if n is a non-negative integer
    if type(n) ~= "number" or n < 0 or n % 1 ~= 0 then
        return nil, "Input must be a non-negative integer"
    end

    local result = 1
    for i = 2, n do
        result = result * i
    end
    return result
end

-- Example usage and error handling
local inputs = {5, 0, -3, 3.5, "text"}
for _, input in ipairs(inputs) do
    local ok, result = pcall(factorial, input)
    if not ok then
        print("Caught error: " .. result)
    else
        if result then
            print("Factorial of " .. input .. " is " .. result)
        else
            print("Error for input " .. input .. ": " .. result)
        end
    end
end