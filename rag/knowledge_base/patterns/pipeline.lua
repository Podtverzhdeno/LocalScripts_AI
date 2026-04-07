-- Data Pipeline Pattern
-- Implements composable data transformation pipeline
-- Use case: ETL processes, data processing, stream processing

-- Pipeline builder
local Pipeline = {}
Pipeline.__index = Pipeline

function Pipeline.new()
    local self = setmetatable({}, Pipeline)
    self.stages = {}
    return self
end

-- Add transformation stage
function Pipeline:pipe(transform)
    table.insert(self.stages, transform)
    return self  -- Allow chaining
end

-- Execute pipeline on data
function Pipeline:execute(data)
    local result = data

    for i, stage in ipairs(self.stages) do
        local success, output = pcall(stage, result)
        if not success then
            return nil, string.format("Stage %d failed: %s", i, output)
        end
        result = output
    end

    return result
end

-- Common transformations
local Transforms = {}

-- Filter items by predicate
function Transforms.filter(predicate)
    return function(items)
        local filtered = {}
        for _, item in ipairs(items) do
            if predicate(item) then
                table.insert(filtered, item)
            end
        end
        return filtered
    end
end

-- Map transformation over items
function Transforms.map(mapper)
    return function(items)
        local mapped = {}
        for i, item in ipairs(items) do
            mapped[i] = mapper(item)
        end
        return mapped
    end
end

-- Reduce items to single value
function Transforms.reduce(reducer, initial)
    return function(items)
        local acc = initial
        for _, item in ipairs(items) do
            acc = reducer(acc, item)
        end
        return acc
    end
end

-- Take first N items
function Transforms.take(n)
    return function(items)
        local result = {}
        for i = 1, math.min(n, #items) do
            result[i] = items[i]
        end
        return result
    end
end

-- Sort items
function Transforms.sort(comparator)
    return function(items)
        local sorted = {}
        for i, v in ipairs(items) do
            sorted[i] = v
        end
        table.sort(sorted, comparator)
        return sorted
    end
end

-- Example usage:
-- local pipeline = Pipeline.new()
--     :pipe(Transforms.filter(function(x) return x > 0 end))
--     :pipe(Transforms.map(function(x) return x * 2 end))
--     :pipe(Transforms.sort(function(a, b) return a < b end))
--     :pipe(Transforms.take(5))
--
-- local data = {-1, 5, 2, -3, 8, 1, 9}
-- local result = pipeline:execute(data)
-- print(table.concat(result, ", "))  -- 2, 4, 10, 16, 18
