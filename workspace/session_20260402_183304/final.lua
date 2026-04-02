-- Define a calculator with basic operations

local calc = {}

function calc.add(x, y)
    return load("return " .. x .. " + " .. y)()
end

function calc.subtract(x, y)
    return load("return " .. x .. " - " .. y)()
end

function calc.multiply(x, y)
    return load("return " .. x .. " * " .. y)()
end

function calc.divide(x, y)
    if y == 0 then
        error("Division by zero")
    end
    return load("return " .. x .. " / " .. y)()
end

-- Example usage
print(calc.add(5, 3))       -- Output: 8
print(calc.subtract(10, 4)) -- Output: 6
print(calc.multiply(7, 2))  -- Output: 14
print(calc.divide(9, 3))    -- Output: 3

-- Test division by zero error handling
pcall(function() calc.divide(5, 0) end)
if pcall(function() calc.divide(5, 0) end) then
    print("No error")
else
    print("Caught division by zero error") -- Expected output
end