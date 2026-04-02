```lua
-- Fibonacci function using memoization to improve performance
local memo = {}

function fibonacci(n)
    -- Check for edge cases
    if n < 0 then
        error("Input must be a non-negative integer")
    elseif n == 0 then
        return 0
    elseif n == 1 then
        return 1
    end

    -- Check if result is already computed and stored in memo table
    if not memo[n] then
        -- Recursively compute the value and store it in memo table
        memo[n] = fibonacci(n - 1) + fibonacci(n - 2)
    end

    return memo[n]
end

-- Example usage:
print(fibonacci(10))  -- Output: 55
```