-- Function to calculate factorial using recursion
local function factorial(n)
    if n == 0 or n == 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

-- Test the factorial function
for i = 0, 6 do
    print(string.format("factorial(%d) = %d", i, factorial(i)))
end