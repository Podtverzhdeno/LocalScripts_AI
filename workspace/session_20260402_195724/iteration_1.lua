-- Simple Calculator in Lua - supports +, -, *, / operations

local Calculator = {}

-- Perform calculation based on operator
function Calculator.calculate(a, b, operator)
    local operators = {
        ["+"] = function(x, y) return x + y end,
        ["-"] = function(x, y) return x - y end,
        ["*"] = function(x, y) return x * y end,
        ["/"] = function(x, y)
            if y == 0 then
                error("Division by zero is not allowed")
            end
            return x / y
        end,
    }

    local fn = operators[operator]
    if not fn then
        error(string.format("Unknown operator: %s", tostring(operator)))
    end

    return fn(a, b)
end

-- Format result for display
function Calculator.formatResult(a, b, op, result)
    return string.format("%.2f %s %.2f = %.2f", a, op, b, result)
end

-- Interactive mode: read from command line arguments or prompt user
function Calculator.run(args)
    -- If arguments provided via command line
    if #args >= 3 then
        local a = tonumber(args[1])
        local op = args[2]
        local b = tonumber(args[3])

        if not a or not b then
            print("Error: Invalid numbers provided")
            return
        end

        local ok, result = pcall(Calculator.calculate, a, b, op)
        if ok then
            print(Calculator.formatResult(a, b, op, result))
        else
            print("Error: " .. result)
        end
        return
    end

    -- Demo mode: show example calculations
    print("=== Calculator Demo ===\n")

    local examples = {
        {10, "+", 5},
        {20, "-", 8},
        {6, "*", 7},
        {15, "/", 3},
        {7, "/", 0},  -- division by zero test
    }

    for _, ex in ipairs(examples) do
        local a, op, b = ex[1], ex[2], ex[3]
        local ok, result = pcall(Calculator.calculate, a, b, op)

        if ok then
            print(Calculator.formatResult(a, b, op, result))
        else
            print(string.format("%.2f %s %.2f -> Error: %s", a, op, b, result))
        end
    end
end

-- Run with command line args or demo mode
Calculator.run({ ... })