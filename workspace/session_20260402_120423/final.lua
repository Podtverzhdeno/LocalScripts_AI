```lua
-- Fibonacci function using iterative approach

function fibonacci(n)
    -- Handle edge cases
    if n < 0 then
        return nil, "Input should be a non-negative integer"
    elseif n == 0 then
        return 0
    elseif n == 1 then
        return 1
    end
    
    local a, b = 0, 1
    for i = 2, n do
        a, b = b, a + b
    end
    return b
end

-- Example usage:
print(fibonacci(10))  -- Output: 55
```