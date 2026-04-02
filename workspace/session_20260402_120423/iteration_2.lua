```lua
-- Fibonacci function in Lua

-- Recursive implementation with memoization to improve performance
local function fibonacci(n, memo)
    -- Base cases
    if n == 0 then return 0 end
    if n == 1 then return 1 end
    
    -- Check if value is already computed
    if memo[n] ~= nil then
        return memo[n]
    else
        -- Compute and store the result in memo table
        local result = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
        memo[n] = result
        return result
    end
end

-- Wrapper function to initialize memoization table
function getFibonacci(n)
    local memo = {}
    return fibonacci(n, memo)
end

-- Example usage
print(getFibonacci(10)) -- Output: 55
```