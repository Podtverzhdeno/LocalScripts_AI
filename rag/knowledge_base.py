"""
Knowledge Base initialization for RAG system.

Contains curated Lua code examples, patterns, and best practices
to reduce hallucinations and improve code quality.
"""

from langchain_core.documents import Document
from typing import List
import logging

logger = logging.getLogger("localscript.rag")


# ============================================================
# Lua Standard Library Examples
# ============================================================

LUA_STDLIB_EXAMPLES = [
    {
        "description": "Table manipulation - insert, remove, sort",
        "code": """local items = {"apple", "banana", "cherry"}
table.insert(items, "date")
table.remove(items, 2)
table.sort(items)
for i, v in ipairs(items) do
    print(i, v)
end""",
        "category": "stdlib",
        "tags": ["table", "array", "sort"]
    },
    {
        "description": "String operations - split, join, pattern matching",
        "code": """local text = "hello,world,lua"
local parts = {}
for part in text:gmatch("[^,]+") do
    table.insert(parts, part)
end

local joined = table.concat(parts, " | ")
print(joined)  -- hello | world | lua""",
        "category": "stdlib",
        "tags": ["string", "split", "pattern"]
    },
    {
        "description": "Math operations - random, floor, ceil, abs",
        "code": """math.randomseed(os.time())
local random_num = math.random(1, 100)
local floored = math.floor(3.7)
local ceiled = math.ceil(3.2)
local absolute = math.abs(-5)
print(random_num, floored, ceiled, absolute)""",
        "category": "stdlib",
        "tags": ["math", "random"]
    },
    {
        "description": "Error handling with pcall and xpcall",
        "code": """local function risky_operation(x)
    if x < 0 then
        error("Negative value not allowed")
    end
    return math.sqrt(x)
end

local ok, result = pcall(risky_operation, 16)
if ok then
    print("Result:", result)
else
    print("Error:", result)
end""",
        "category": "stdlib",
        "tags": ["error", "pcall", "exception"]
    }
]


# ============================================================
# Algorithm Examples
# ============================================================

ALGORITHM_EXAMPLES = [
    {
        "description": "Fibonacci with memoization",
        "code": """local memo = {}
local function fibonacci(n)
    if n <= 1 then return n end
    if memo[n] then return memo[n] end
    memo[n] = fibonacci(n-1) + fibonacci(n-2)
    return memo[n]
end

for i = 0, 10 do
    print(string.format("fib(%d) = %d", i, fibonacci(i)))
end""",
        "category": "algorithm",
        "tags": ["fibonacci", "memoization", "recursion", "optimization"]
    },
    {
        "description": "Binary search in sorted array",
        "code": """local function binary_search(arr, target)
    local left, right = 1, #arr
    while left <= right do
        local mid = math.floor((left + right) / 2)
        if arr[mid] == target then
            return mid
        elseif arr[mid] < target then
            left = mid + 1
        else
            right = mid - 1
        end
    end
    return nil
end

local numbers = {1, 3, 5, 7, 9, 11, 13}
print(binary_search(numbers, 7))  -- 4""",
        "category": "algorithm",
        "tags": ["search", "binary-search", "array"]
    },
    {
        "description": "Quicksort implementation",
        "code": """local function quicksort(arr, low, high)
    if low < high then
        local pivot = arr[high]
        local i = low - 1

        for j = low, high - 1 do
            if arr[j] <= pivot then
                i = i + 1
                arr[i], arr[j] = arr[j], arr[i]
            end
        end

        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        local pi = i + 1

        quicksort(arr, low, pi - 1)
        quicksort(arr, pi + 1, high)
    end
end

local data = {64, 34, 25, 12, 22, 11, 90}
quicksort(data, 1, #data)
print(table.concat(data, ", "))""",
        "category": "algorithm",
        "tags": ["sort", "quicksort", "recursion"]
    }
]


# ============================================================
# Design Patterns
# ============================================================

PATTERN_EXAMPLES = [
    {
        "description": "Module pattern - encapsulation and namespacing",
        "code": """local Calculator = {}

function Calculator.add(a, b)
    return a + b
end

function Calculator.subtract(a, b)
    return a - b
end

function Calculator.multiply(a, b)
    return a * b
end

function Calculator.divide(a, b)
    if b == 0 then
        error("Division by zero")
    end
    return a / b
end

return Calculator""",
        "category": "pattern",
        "tags": ["module", "encapsulation", "oop"]
    },
    {
        "description": "Factory pattern - object creation",
        "code": """local function createAnimal(type, name)
    local animal = {
        type = type,
        name = name
    }

    function animal:speak()
        if self.type == "dog" then
            return self.name .. " says: Woof!"
        elseif self.type == "cat" then
            return self.name .. " says: Meow!"
        else
            return self.name .. " makes a sound"
        end
    end

    return animal
end

local dog = createAnimal("dog", "Rex")
local cat = createAnimal("cat", "Whiskers")
print(dog:speak())
print(cat:speak())""",
        "category": "pattern",
        "tags": ["factory", "oop", "constructor"]
    },
    {
        "description": "Iterator pattern - custom iteration",
        "code": """local function range(from, to, step)
    step = step or 1
    return function(_, current)
        current = current + step
        if current <= to then
            return current
        end
    end, nil, from - step
end

for i in range(1, 10, 2) do
    print(i)  -- 1, 3, 5, 7, 9
end""",
        "category": "pattern",
        "tags": ["iterator", "generator", "functional"]
    }
]


# ============================================================
# Data Structures
# ============================================================

DATA_STRUCTURE_EXAMPLES = [
    {
        "description": "Stack implementation",
        "code": """local Stack = {}
Stack.__index = Stack

function Stack.new()
    return setmetatable({items = {}}, Stack)
end

function Stack:push(item)
    table.insert(self.items, item)
end

function Stack:pop()
    return table.remove(self.items)
end

function Stack:peek()
    return self.items[#self.items]
end

function Stack:is_empty()
    return #self.items == 0
end

local stack = Stack.new()
stack:push(1)
stack:push(2)
print(stack:pop())  -- 2""",
        "category": "data-structure",
        "tags": ["stack", "oop", "collection"]
    },
    {
        "description": "Queue implementation",
        "code": """local Queue = {}
Queue.__index = Queue

function Queue.new()
    return setmetatable({items = {}, head = 1, tail = 0}, Queue)
end

function Queue:enqueue(item)
    self.tail = self.tail + 1
    self.items[self.tail] = item
end

function Queue:dequeue()
    if self:is_empty() then return nil end
    local item = self.items[self.head]
    self.items[self.head] = nil
    self.head = self.head + 1
    return item
end

function Queue:is_empty()
    return self.head > self.tail
end

local queue = Queue.new()
queue:enqueue("first")
queue:enqueue("second")
print(queue:dequeue())  -- first""",
        "category": "data-structure",
        "tags": ["queue", "oop", "collection"]
    }
]


# ============================================================
# Best Practices
# ============================================================

BEST_PRACTICE_EXAMPLES = [
    {
        "description": "Use local variables for performance",
        "code": """-- GOOD: local variables are faster
local function calculate(n)
    local result = 0
    for i = 1, n do
        result = result + i
    end
    return result
end

-- BAD: global variables are slower
function calculate_bad(n)
    result = 0  -- global!
    for i = 1, n do
        result = result + i
    end
    return result
end""",
        "category": "best-practice",
        "tags": ["performance", "local", "scope"]
    },
    {
        "description": "Proper error handling and validation",
        "code": """local function divide(a, b)
    -- Validate input types
    if type(a) ~= "number" or type(b) ~= "number" then
        error("Both arguments must be numbers")
    end

    -- Check for division by zero
    if b == 0 then
        error("Division by zero is not allowed")
    end

    return a / b
end

-- Safe usage with pcall
local ok, result = pcall(divide, 10, 2)
if ok then
    print("Result:", result)
else
    print("Error:", result)
end""",
        "category": "best-practice",
        "tags": ["error-handling", "validation", "robustness"]
    }
]


# ============================================================
# Advanced Algorithms
# ============================================================

ADVANCED_ALGORITHM_EXAMPLES = [
    {
        "description": "Merge sort implementation",
        "code": """local function merge(left, right)
    local result = {}
    local i, j = 1, 1

    while i <= #left and j <= #right do
        if left[i] <= right[j] then
            table.insert(result, left[i])
            i = i + 1
        else
            table.insert(result, right[j])
            j = j + 1
        end
    end

    while i <= #left do
        table.insert(result, left[i])
        i = i + 1
    end

    while j <= #right do
        table.insert(result, right[j])
        j = j + 1
    end

    return result
end

local function mergesort(arr)
    if #arr <= 1 then return arr end

    local mid = math.floor(#arr / 2)
    local left = {table.unpack(arr, 1, mid)}
    local right = {table.unpack(arr, mid + 1)}

    return merge(mergesort(left), mergesort(right))
end

local data = {38, 27, 43, 3, 9, 82, 10}
local sorted = mergesort(data)
print(table.concat(sorted, ", "))""",
        "category": "algorithm",
        "tags": ["sort", "mergesort", "recursion", "divide-conquer"]
    },
    {
        "description": "Depth-first search (DFS) for graphs",
        "code": """local function dfs(graph, start, visited)
    visited = visited or {}
    visited[start] = true
    print("Visiting:", start)

    for _, neighbor in ipairs(graph[start] or {}) do
        if not visited[neighbor] then
            dfs(graph, neighbor, visited)
        end
    end

    return visited
end

-- Example graph (adjacency list)
local graph = {
    A = {"B", "C"},
    B = {"D", "E"},
    C = {"F"},
    D = {},
    E = {"F"},
    F = {}
}

dfs(graph, "A")""",
        "category": "algorithm",
        "tags": ["graph", "dfs", "traversal", "recursion"]
    },
    {
        "description": "Breadth-first search (BFS) for graphs",
        "code": """local function bfs(graph, start)
    local visited = {}
    local queue = {start}
    local head = 1

    visited[start] = true

    while head <= #queue do
        local node = queue[head]
        head = head + 1
        print("Visiting:", node)

        for _, neighbor in ipairs(graph[node] or {}) do
            if not visited[neighbor] then
                visited[neighbor] = true
                table.insert(queue, neighbor)
            end
        end
    end

    return visited
end

-- Example graph
local graph = {
    A = {"B", "C"},
    B = {"D", "E"},
    C = {"F"},
    D = {},
    E = {"F"},
    F = {}
}

bfs(graph, "A")""",
        "category": "algorithm",
        "tags": ["graph", "bfs", "traversal", "queue"]
    },
    {
        "description": "Dynamic programming - longest common subsequence",
        "code": """local function lcs(s1, s2)
    local m, n = #s1, #s2
    local dp = {}

    -- Initialize DP table
    for i = 0, m do
        dp[i] = {}
        for j = 0, n do
            dp[i][j] = 0
        end
    end

    -- Fill DP table
    for i = 1, m do
        for j = 1, n do
            if s1:sub(i, i) == s2:sub(j, j) then
                dp[i][j] = dp[i-1][j-1] + 1
            else
                dp[i][j] = math.max(dp[i-1][j], dp[i][j-1])
            end
        end
    end

    return dp[m][n]
end

local str1 = "ABCDGH"
local str2 = "AEDFHR"
print("LCS length:", lcs(str1, str2))  -- 3 (ADH)""",
        "category": "algorithm",
        "tags": ["dynamic-programming", "lcs", "optimization"]
    }
]


# ============================================================
# File I/O and System Operations
# ============================================================

FILE_IO_EXAMPLES = [
    {
        "description": "Reading file line by line",
        "code": """local function read_file(filename)
    local file = io.open(filename, "r")
    if not file then
        return nil, "Could not open file"
    end

    local lines = {}
    for line in file:lines() do
        table.insert(lines, line)
    end

    file:close()
    return lines
end

local lines, err = read_file("data.txt")
if lines then
    for i, line in ipairs(lines) do
        print(i, line)
    end
else
    print("Error:", err)
end""",
        "category": "file-io",
        "tags": ["file", "read", "io", "lines"]
    },
    {
        "description": "Writing to file with error handling",
        "code": """local function write_file(filename, content)
    local file, err = io.open(filename, "w")
    if not file then
        return false, "Could not open file: " .. err
    end

    local success, write_err = pcall(function()
        file:write(content)
    end)

    file:close()

    if not success then
        return false, "Write error: " .. write_err
    end

    return true
end

local ok, err = write_file("output.txt", "Hello, World!")
if ok then
    print("File written successfully")
else
    print("Error:", err)
end""",
        "category": "file-io",
        "tags": ["file", "write", "io", "error-handling"]
    },
    {
        "description": "JSON-like data serialization",
        "code": """local function serialize(data, indent)
    indent = indent or 0
    local spacing = string.rep("  ", indent)

    if type(data) == "table" then
        local result = "{\n"
        for k, v in pairs(data) do
            result = result .. spacing .. "  " .. tostring(k) .. " = "
            result = result .. serialize(v, indent + 1) .. ",\n"
        end
        result = result .. spacing .. "}"
        return result
    elseif type(data) == "string" then
        return string.format("%q", data)
    else
        return tostring(data)
    end
end

local data = {
    name = "John",
    age = 30,
    skills = {"Lua", "Python", "Go"}
}

print(serialize(data))""",
        "category": "file-io",
        "tags": ["serialization", "table", "format"]
    }
]


# ============================================================
# Metatable and OOP Patterns
# ============================================================

METATABLE_EXAMPLES = [
    {
        "description": "Class-like OOP with metatables",
        "code": """local Animal = {}
Animal.__index = Animal

function Animal.new(name, sound)
    local self = setmetatable({}, Animal)
    self.name = name
    self.sound = sound
    return self
end

function Animal:speak()
    print(self.name .. " says: " .. self.sound)
end

function Animal:get_name()
    return self.name
end

-- Usage
local dog = Animal.new("Rex", "Woof!")
local cat = Animal.new("Whiskers", "Meow!")

dog:speak()  -- Rex says: Woof!
cat:speak()  -- Whiskers says: Meow!""",
        "category": "oop",
        "tags": ["metatable", "class", "oop", "constructor"]
    },
    {
        "description": "Inheritance with metatables",
        "code": """-- Base class
local Animal = {}
Animal.__index = Animal

function Animal.new(name)
    local self = setmetatable({}, Animal)
    self.name = name
    return self
end

function Animal:speak()
    print(self.name .. " makes a sound")
end

-- Derived class
local Dog = setmetatable({}, {__index = Animal})
Dog.__index = Dog

function Dog.new(name, breed)
    local self = Animal.new(name)
    setmetatable(self, Dog)
    self.breed = breed
    return self
end

function Dog:speak()
    print(self.name .. " barks!")
end

function Dog:get_breed()
    return self.breed
end

-- Usage
local dog = Dog.new("Rex", "Labrador")
dog:speak()  -- Rex barks!
print(dog:get_breed())  -- Labrador""",
        "category": "oop",
        "tags": ["metatable", "inheritance", "oop", "polymorphism"]
    },
    {
        "description": "Operator overloading with metatables",
        "code": """local Vector = {}
Vector.__index = Vector

function Vector.new(x, y)
    local self = setmetatable({}, Vector)
    self.x = x
    self.y = y
    return self
end

function Vector.__add(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

function Vector.__sub(a, b)
    return Vector.new(a.x - b.x, a.y - b.y)
end

function Vector.__tostring(v)
    return string.format("Vector(%d, %d)", v.x, v.y)
end

-- Usage
local v1 = Vector.new(3, 4)
local v2 = Vector.new(1, 2)
local v3 = v1 + v2

print(v3)  -- Vector(4, 6)""",
        "category": "oop",
        "tags": ["metatable", "operator-overload", "vector"]
    }
]


# ============================================================
# Coroutines and Async Patterns
# ============================================================

COROUTINE_EXAMPLES = [
    {
        "description": "Basic coroutine usage",
        "code": """local function counter()
    local i = 0
    while true do
        i = i + 1
        coroutine.yield(i)
    end
end

local co = coroutine.create(counter)

for i = 1, 5 do
    local ok, value = coroutine.resume(co)
    print("Count:", value)
end""",
        "category": "coroutine",
        "tags": ["coroutine", "yield", "generator"]
    },
    {
        "description": "Producer-consumer pattern with coroutines",
        "code": """local function producer()
    return coroutine.create(function()
        for i = 1, 5 do
            print("Producing:", i)
            coroutine.yield(i)
        end
    end)
end

local function consumer(prod)
    while true do
        local ok, value = coroutine.resume(prod)
        if not ok or value == nil then break end
        print("Consuming:", value)
    end
end

local prod = producer()
consumer(prod)""",
        "category": "coroutine",
        "tags": ["coroutine", "producer-consumer", "pattern"]
    }
]


# ============================================================
# String Processing and Patterns
# ============================================================

STRING_PROCESSING_EXAMPLES = [
    {
        "description": "Advanced pattern matching and capture",
        "code": """local text = "Email: john@example.com, Phone: 123-456-7890"

-- Extract email
local email = text:match("([%w%.]+@[%w%.]+)")
print("Email:", email)

-- Extract phone
local phone = text:match("(%d+%-%d+%-%d+)")
print("Phone:", phone)

-- Multiple captures
local name, domain = email:match("([^@]+)@(.+)")
print("Name:", name, "Domain:", domain)""",
        "category": "string",
        "tags": ["pattern", "regex", "capture", "parsing"]
    },
    {
        "description": "String substitution and replacement",
        "code": """local text = "Hello, {name}! Welcome to {place}."

-- Simple replacement
local result = text:gsub("{name}", "Alice")
                    :gsub("{place}", "Wonderland")
print(result)

-- Pattern-based replacement
local html = "<p>Hello</p><p>World</p>"
local plain = html:gsub("<[^>]+>", "")
print(plain)  -- HelloWorld

-- Function-based replacement
local numbers = "1 2 3 4 5"
local doubled = numbers:gsub("%d+", function(n)
    return tostring(tonumber(n) * 2)
end)
print(doubled)  -- 2 4 6 8 10""",
        "category": "string",
        "tags": ["gsub", "replacement", "pattern"]
    }
]



# ============================================================
# Tabular Data Processing Examples
# ============================================================

TABLE_DATA_EXAMPLES = [
    {
        "description": "Processing tabular data with headers - skip first row",
        "code": """-- Data with header row
local data = {
    {"Name", "Age", "City"},      -- Header row
    {"Alice", 30, "New York"},
    {"Bob", 25, "Los Angeles"},
    {"Charlie", 35, "Chicago"}
}

-- Filter by age, skipping header
local function filterByAge(data, minAge, maxAge)
    local results = {}
    for i = 2, #data do  -- Start from 2 to skip header
        local row = data[i]
        local age = row[2]
        if age >= minAge and age <= maxAge then
            table.insert(results, row)
        end
    end
    return results
end

local filtered = filterByAge(data, 26, 34)
for _, row in ipairs(filtered) do
    print(row[1], row[2], row[3])
end""",
        "category": "table_data",
        "tags": ["table", "data", "filter", "header", "csv"]
    },
    {
        "description": "Safe data filtering with type checking",
        "code": """local function filterData(data, predicate)
    local results = {}
    for i, row in ipairs(data) do
        -- Skip header (first row) or non-table rows
        if i > 1 and type(row) == "table" then
            if predicate(row) then
                table.insert(results, row)
            end
        end
    end
    return results
end

-- Example: filter by numeric age
local data = {
    {"Name", "Age", "City"},
    {"Alice", "30", "New York"},
    {"Bob", "25", "Los Angeles"}
}

local filtered = filterData(data, function(row)
    local age = tonumber(row[2])
    return age and age >= 26 and age <= 34
end)""",
        "category": "table_data",
        "tags": ["table", "filter", "type-check", "safe"]
    },
    {
        "description": "Table data with column mapping",
        "code": """-- Define column indices for readability
local COL = {
    NAME = 1,
    AGE = 2,
    CITY = 3
}

local data = {
    {"Name", "Age", "City"},
    {"Alice", 30, "New York"},
    {"Bob", 25, "Los Angeles"}
}

-- Process data using column constants
for i = 2, #data do  -- Skip header
    local row = data[i]
    local name = row[COL.NAME]
    local age = row[COL.AGE]
    local city = row[COL.CITY]

    if age >= 25 then
        print(string.format("%s (%d) from %s", name, age, city))
    end
end""",
        "category": "table_data",
        "tags": ["table", "columns", "constants", "readable"]
    },
    {
        "description": "CSV-like data handler class",
        "code": """local DataHandler = {}
DataHandler.__index = DataHandler

function DataHandler.new(data, hasHeader)
    local self = setmetatable({}, DataHandler)
    self.data = data
    self.hasHeader = hasHeader or true
    self.startRow = hasHeader and 2 or 1
    return self
end

function DataHandler:filter(columnIndex, predicate)
    local results = {}
    for i = self.startRow, #self.data do
        local row = self.data[i]
        local value = row[columnIndex]
        if predicate(value) then
            table.insert(results, row)
        end
    end
    return results
end

-- Usage
local data = {
    {"Name", "Age", "City"},
    {"Alice", 30, "New York"},
    {"Bob", 25, "Los Angeles"}
}

local handler = DataHandler.new(data, true)
local adults = handler:filter(2, function(age)
    return age >= 18
end)""",
        "category": "table_data",
        "tags": ["table", "class", "oop", "csv", "handler"]
    }
]


# ============================================================
# Low-Code Patterns (MTS Hackathon 2026)
# ============================================================

LOWCODE_PATTERN_EXAMPLES = [
    {
        "description": "Get last element from array (wf.vars context)",
        "code": """-- Task: Из полученного списка email получи последний
-- Context: wf.vars.emails = ["user1@example.com", "user2@example.com", "user3@example.com"]

-- Solution: Use Lua's # operator to get array length
return wf.vars.emails[#wf.vars.emails]

-- Explanation:
-- #wf.vars.emails returns the length of the array (3)
-- wf.vars.emails[3] returns the last element""",
        "category": "lowcode",
        "tags": ["array", "last-element", "wf.vars", "simple"]
    },
    {
        "description": "Increment counter variable (wf.vars context)",
        "code": """-- Task: Увеличивай значение переменной try_count_n на каждой итерации
-- Context: wf.vars.try_count_n = 3

-- Solution: Simple increment
return wf.vars.try_count_n + 1

-- Result: 4
-- Note: This returns the new value, doesn't modify wf.vars directly""",
        "category": "lowcode",
        "tags": ["counter", "increment", "wf.vars", "simple"]
    },
    {
        "description": "Clear specific fields in nested object (wf.vars context)",
        "code": """-- Task: Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL
-- Context: wf.vars.RESTbody = {result = [{ID = 123, ENTITY_ID = 456, CALL = "example", OTHER = "value"}]}

-- Solution: Set specific fields to nil
local data = wf.vars.RESTbody.result[1]
data.ID = nil
data.ENTITY_ID = nil
data.CALL = nil

return data
-- Result: {OTHER = "value"}""",
        "category": "lowcode",
        "tags": ["object", "clear", "nil", "wf.vars", "rest"]
    },
    {
        "description": "Filter array by field value (wf.vars context)",
        "code": """-- Task: Из полученного массива users оставь только тех, у кого поле active равно true
-- Context: wf.vars.users = [{name="Alice", active=true}, {name="Bob", active=false}, {name="Charlie", active=true}]

-- Solution: Filter with loop
local result = _utils.array.new()
for _, user in ipairs(wf.vars.users) do
    if user.active == true then
        table.insert(result, user)
    end
end

return result
-- Result: [{name="Alice", active=true}, {name="Charlie", active=true}]""",
        "category": "lowcode",
        "tags": ["array", "filter", "wf.vars", "loop"]
    },
    {
        "description": "Concatenate strings with space (wf.vars context)",
        "code": """-- Task: Объедини имя и фамилию пользователя в одну строку через пробел
-- Context: wf.vars.first_name = "Иван", wf.vars.last_name = "Петров"

-- Solution: Use .. operator for concatenation
return wf.vars.first_name .. " " .. wf.vars.last_name

-- Result: "Иван Петров"
-- Note: .. is Lua's string concatenation operator""",
        "category": "lowcode",
        "tags": ["string", "concatenate", "wf.vars", "simple"]
    },
    {
        "description": "Validate email format (wf.vars context)",
        "code": """-- Task: Проверь, является ли строка валидным email адресом
-- Context: wf.vars.email = "test@example.com"

-- Solution: Check for @ symbol and basic structure
local email = wf.vars.email

-- Basic validation: must contain @ and have text before and after
local has_at = string.find(email, "@") ~= nil
local parts = {}
for part in string.gmatch(email, "[^@]+") do
    table.insert(parts, part)
end

-- Valid if: has @, exactly 2 parts, both parts non-empty
local is_valid = has_at and #parts == 2 and #parts[1] > 0 and #parts[2] > 0

return is_valid
-- Result: true""",
        "category": "lowcode",
        "tags": ["string", "validation", "email", "wf.vars"]
    },
    {
        "description": "Sum all numbers in array (wf.vars context)",
        "code": """-- Task: Посчитай сумму всех чисел в массиве numbers
-- Context: wf.vars.numbers = [10, 20, 30, 40, 50]

-- Solution: Loop and accumulate
local sum = 0
for _, num in ipairs(wf.vars.numbers) do
    sum = sum + num
end

return sum
-- Result: 150""",
        "category": "lowcode",
        "tags": ["array", "sum", "loop", "wf.vars", "math"]
    },
    {
        "description": "Format Unix timestamp to DD.MM.YYYY (wf.vars context)",
        "code": """-- Task: Преобразуй timestamp в читаемый формат даты DD.MM.YYYY
-- Context: wf.vars.timestamp = 1609459200

-- Solution: Use os.date with format string
local timestamp = wf.vars.timestamp
local date_table = os.date("*t", timestamp)

-- Format as DD.MM.YYYY
local formatted = string.format(
    "%02d.%02d.%04d",
    date_table.day,
    date_table.month,
    date_table.year
)

return formatted
-- Result: "01.01.2021"
-- Note: os.date("*t", timestamp) returns a table with day, month, year fields""",
        "category": "lowcode",
        "tags": ["date", "timestamp", "format", "wf.vars", "os.date"]
    }
]


# ============================================================
# LowCode Best Practices (MTS Octapi)
# ============================================================

LOWCODE_BEST_PRACTICES = [
    {
        "description": "Always use wf.vars for variable access in LowCode",
        "code": """-- GOOD: Access variables through wf.vars
local email = wf.vars.user_email
local count = wf.vars.try_count_n

-- BAD: Direct variable access (won't work in LowCode)
-- local email = user_email  -- ERROR: undefined variable

-- GOOD: Return values directly
return wf.vars.emails[#wf.vars.emails]

-- GOOD: Modify and return
local data = wf.vars.data
data.processed = true
return data""",
        "category": "lowcode",
        "tags": ["best-practice", "wf.vars", "access-pattern"]
    },
    {
        "description": "Use _utils.array for array creation in LowCode",
        "code": """-- GOOD: Create arrays with _utils.array.new()
local result = _utils.array.new()
for _, item in ipairs(wf.vars.items) do
    if item.active then
        table.insert(result, item)
    end
end
return result

-- GOOD: Mark existing table as array
local data = {1, 2, 3}
_utils.array.markAsArray(data)
return data

-- BAD: Plain table might not be recognized as array
-- return {1, 2, 3}  -- May cause issues in LowCode""",
        "category": "lowcode",
        "tags": ["best-practice", "array", "_utils", "lowcode-specific"]
    },
    {
        "description": "Handle nil values safely in LowCode",
        "code": """-- GOOD: Check for nil before accessing
local email = wf.vars.user and wf.vars.user.email or "default@example.com"

-- GOOD: Use pcall for risky operations
local ok, result = pcall(function()
    return wf.vars.data.nested.field
end)
if ok then
    return result
else
    return nil
end

-- GOOD: Provide defaults
local count = wf.vars.count or 0
return count + 1

-- BAD: Direct access without checking
-- return wf.vars.user.email  -- ERROR if user is nil""",
        "category": "lowcode",
        "tags": ["best-practice", "nil-handling", "safety", "error-handling"]
    },
    {
        "description": "Efficient string operations in LowCode",
        "code": """-- GOOD: Use string.format for complex formatting
local name = wf.vars.first_name
local age = wf.vars.age
return string.format("%s is %d years old", name, age)

-- GOOD: Use table.concat for multiple concatenations
local parts = {wf.vars.first_name, wf.vars.middle_name, wf.vars.last_name}
return table.concat(parts, " ")

-- BAD: Multiple .. operations (slower)
-- return wf.vars.first_name .. " " .. wf.vars.middle_name .. " " .. wf.vars.last_name

-- GOOD: Pattern matching for validation
local email = wf.vars.email
return string.match(email, "^[%w%._%+%-]+@[%w%.%-]+%.%w+$") ~= nil""",
        "category": "lowcode",
        "tags": ["best-practice", "string", "performance", "format"]
    }
]


# ============================================================
# Event-driven architecture with event emitter
# ============================================================

LOWCODE_INTEGRATION_EXAMPLES = [
    {
        "description": "Event-driven architecture with event emitter",
        "code": """local EventEmitter = {}
EventEmitter.__index = EventEmitter

function EventEmitter.new()
    local self = setmetatable({}, EventEmitter)
    self.listeners = {}
    return self
end

function EventEmitter:on(event, callback)
    if not self.listeners[event] then
        self.listeners[event] = {}
    end
    table.insert(self.listeners[event], callback)
end

function EventEmitter:emit(event, ...)
    if not self.listeners[event] then return end
    for _, callback in ipairs(self.listeners[event]) do
        pcall(callback, ...)
    end
end

function EventEmitter:once(event, callback)
    local wrapper
    wrapper = function(...)
        callback(...)
        self:off(event, wrapper)
    end
    self:on(event, wrapper)
end""",
        "category": "pattern",
        "tags": ["event-driven", "observer", "pub-sub", "decoupling"]
    },
    {
        "description": "Data pipeline with composable transformations",
        "code": """local Pipeline = {}
Pipeline.__index = Pipeline

function Pipeline.new()
    local self = setmetatable({}, Pipeline)
    self.stages = {}
    return self
end

function Pipeline:pipe(transform)
    table.insert(self.stages, transform)
    return self
end

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

function Transforms.map(mapper)
    return function(items)
        local mapped = {}
        for i, item in ipairs(items) do
            mapped[i] = mapper(item)
        end
        return mapped
    end
end""",
        "category": "pattern",
        "tags": ["pipeline", "etl", "data-processing", "functional"]
    },
    {
        "description": "Retry logic with exponential backoff",
        "code": """function retry_with_backoff(func, config)
    config = config or {
        max_attempts = 3,
        initial_delay = 1,
        max_delay = 60,
        backoff_factor = 2,
        jitter = true
    }

    local attempts = 0
    local delay = config.initial_delay

    while attempts < config.max_attempts do
        attempts = attempts + 1
        local success, result = pcall(func)

        if success then
            return result, nil
        end

        if attempts >= config.max_attempts then
            return nil, string.format("Failed after %d attempts: %s", attempts, result)
        end

        local wait_time = math.min(delay, config.max_delay)
        if config.jitter then
            wait_time = wait_time * (0.5 + math.random() * 0.5)
        end

        -- Wait before retry
        local start = os.time()
        while os.time() - start < wait_time do end

        delay = delay * config.backoff_factor
    end
end""",
        "category": "pattern",
        "tags": ["retry", "resilience", "backoff", "fault-tolerance"]
    },
    {
        "description": "Circuit breaker for fault tolerance",
        "code": """local CircuitBreaker = {}
CircuitBreaker.__index = CircuitBreaker

function CircuitBreaker.new(config)
    local self = setmetatable({}, CircuitBreaker)
    self.failure_threshold = config.failure_threshold or 5
    self.success_threshold = config.success_threshold or 2
    self.timeout = config.timeout or 60
    self.state = "CLOSED"
    self.failure_count = 0
    self.success_count = 0
    self.last_failure_time = 0
    return self
end

function CircuitBreaker:call(func)
    if self.state == "OPEN" then
        if os.time() - self.last_failure_time >= self.timeout then
            self.state = "HALF_OPEN"
        else
            return nil, "Circuit breaker is OPEN"
        end
    end

    local success, result = pcall(func)

    if success then
        self:on_success()
        return result, nil
    else
        self:on_failure()
        return nil, result
    end
end

function CircuitBreaker:on_success()
    self.failure_count = 0
    if self.state == "HALF_OPEN" then
        self.success_count = self.success_count + 1
        if self.success_count >= self.success_threshold then
            self.state = "CLOSED"
        end
    end
end

function CircuitBreaker:on_failure()
    self.failure_count = self.failure_count + 1
    self.last_failure_time = os.time()
    if self.failure_count >= self.failure_threshold then
        self.state = "OPEN"
    end
end""",
        "category": "pattern",
        "tags": ["circuit-breaker", "resilience", "fault-tolerance", "microservices"]
    },
    {
        "description": "Rate limiter with token bucket algorithm",
        "code": """local TokenBucket = {}
TokenBucket.__index = TokenBucket

function TokenBucket.new(capacity, refill_rate)
    local self = setmetatable({}, TokenBucket)
    self.capacity = capacity
    self.tokens = capacity
    self.refill_rate = refill_rate
    self.last_refill = os.time()
    return self
end

function TokenBucket:consume(tokens)
    tokens = tokens or 1
    self:refill()

    if self.tokens >= tokens then
        self.tokens = self.tokens - tokens
        return true
    end
    return false
end

function TokenBucket:refill()
    local now = os.time()
    local elapsed = now - self.last_refill

    if elapsed > 0 then
        local new_tokens = elapsed * self.refill_rate
        self.tokens = math.min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    end
end

function TokenBucket:available()
    self:refill()
    return self.tokens
end""",
        "category": "pattern",
        "tags": ["rate-limiting", "throttling", "token-bucket", "api-protection"]
    },
    {
        "description": "Error handling with Result type and validation",
        "code": """local Result = {}
Result.__index = Result

function Result.ok(value)
    return setmetatable({success = true, value = value}, Result)
end

function Result.err(error)
    return setmetatable({success = false, error = error}, Result)
end

function Result:is_ok()
    return self.success
end

function Result:unwrap()
    if self.success then
        return self.value
    else
        error("Called unwrap on error: " .. tostring(self.error))
    end
end

function Result:unwrap_or(default)
    return self.success and self.value or default
end

function Result:map(func)
    if self.success then
        return Result.ok(func(self.value))
    else
        return self
    end
end

-- Validator for multiple errors
local Validator = {}
Validator.__index = Validator

function Validator.new()
    local self = setmetatable({}, Validator)
    self.errors = {}
    return self
end

function Validator:add_error(field, message)
    if not self.errors[field] then
        self.errors[field] = {}
    end
    table.insert(self.errors[field], message)
end

function Validator:is_valid()
    return next(self.errors) == nil
end""",
        "category": "pattern",
        "tags": ["error-handling", "validation", "result-type", "robustness"]
    }
]


# ============================================================
# Integration Patterns (MTS Hackathon 2026)
# ============================================================

INTEGRATION_EXAMPLES = [
    {
        "description": "Email validation with RFC 5322 rules",
        "code": """function validate_email(email)
    if type(email) ~= "string" then
        return false
    end

    -- Check basic structure: local@domain
    local pattern = "^[%w%._%+%-]+@[%w%.%-]+%.%w+$"
    if not string.match(email, pattern) then
        return false
    end

    -- Additional checks
    local local_part, domain = email:match("^(.+)@(.+)$")

    -- Local part should not start or end with dot
    if local_part:match("^%.") or local_part:match("%.$") then
        return false
    end

    -- No consecutive dots
    if local_part:match("%.%.") then
        return false
    end

    -- Domain should have at least one dot
    if not domain:match("%.") then
        return false
    end

    return true
end

-- Batch validation
function validate_emails(email_list)
    local results = {}
    for i, email in ipairs(email_list) do
        results[i] = {
            email = email,
            valid = validate_email(email)
        }
    end
    return results
end""",
        "category": "integration",
        "tags": ["email", "validation", "rfc5322", "form", "input"]
    },
    {
        "description": "Kafka message producer - format data for message queue",
        "code": """-- Format phone number for Kafka message
function format_phone_for_kafka(phone)
    -- Remove all non-digit characters
    local normalized = phone:gsub("[^%d]", "")

    -- Ensure it starts with country code
    if #normalized == 10 then
        normalized = "7" .. normalized  -- Add Russia country code
    end

    return {
        topic = "phone_numbers",
        key = normalized,
        value = {
            phone = normalized,
            original = phone,
            timestamp = os.time(),
            source = "lua_integration"
        }
    }
end

-- Generic Kafka message formatter
function create_kafka_message(topic, key, data)
    return {
        topic = topic,
        key = key or "",
        value = data,
        timestamp = os.time(),
        headers = {
            ["content-type"] = "application/json",
            ["producer"] = "localscript"
        }
    }
end

-- Serialize message to JSON-like string
function serialize_kafka_message(message)
    local parts = {}
    table.insert(parts, string.format('"topic":"%s"', message.topic))
    table.insert(parts, string.format('"key":"%s"', message.key))
    table.insert(parts, string.format('"timestamp":%d', message.timestamp))
    return "{" .. table.concat(parts, ",") .. "}"
end""",
        "category": "integration",
        "tags": ["kafka", "message-queue", "producer", "event-streaming"]
    },
    {
        "description": "REST API client for user service",
        "code": """-- Create HTTP request structure
function create_http_request(method, url, body, headers)
    local request = {
        method = method or "GET",
        url = url,
        headers = headers or {},
        body = body
    }

    -- Add default headers
    if not request.headers["Content-Type"] and body then
        request.headers["Content-Type"] = "application/json"
    end
    if not request.headers["User-Agent"] then
        request.headers["User-Agent"] = "LocalScript/1.0"
    end

    return request
end

-- User service API client
function create_user_api_client(base_url)
    local client = {
        base_url = base_url
    }

    -- Get user by ID
    function client:get_user(user_id)
        local url = self.base_url .. "/users/" .. tostring(user_id)
        return create_http_request("GET", url)
    end

    -- Create new user
    function client:create_user(user_data)
        local url = self.base_url .. "/users"
        local body = string.format(
            '{"name":"%s","email":"%s","role":"%s"}',
            user_data.name,
            user_data.email,
            user_data.role or "user"
        )
        return create_http_request("POST", url, body)
    end

    -- Update user
    function client:update_user(user_id, user_data)
        local url = self.base_url .. "/users/" .. tostring(user_id)
        local body = string.format('{"name":"%s","email":"%s"}', user_data.name, user_data.email)
        return create_http_request("PUT", url, body)
    end

    return client
end""",
        "category": "integration",
        "tags": ["http", "rest-api", "client", "crud", "microservices"]
    },
    {
        "description": "JSON data transformer between API formats",
        "code": """-- Transform user object from API A to API B format
function transform_user_format(source_json)
    -- Parse source format: {user: {name, email, phone}}
    local name = source_json:match('"name":"([^"]+)"')
    local email = source_json:match('"email":"([^"]+)"')
    local phone = source_json:match('"phone":"([^"]+)"')

    -- Build target format: {fullName, contact: {email, phone}}
    local target = string.format(
        '{"fullName":"%s","contact":{"email":"%s","phone":"%s"}}',
        name or "",
        email or "",
        phone or ""
    )

    return target
end

-- Generic field mapper
function map_fields(source_json, field_mapping)
    local result = {}

    for source_field, target_field in pairs(field_mapping) do
        local pattern = string.format('"%s":"([^"]+)"', source_field)
        local value = source_json:match(pattern)
        if value then
            result[target_field] = value
        end
    end

    return result
end

-- Flatten nested structure
function flatten_json(nested_json, prefix)
    prefix = prefix or ""
    local flat = {}

    -- Extract nested user object
    local user_block = nested_json:match('"user":%{(.-)%}')
    if user_block then
        for key, value in user_block:gmatch('"([^"]+)":"([^"]+)"') do
            flat[prefix .. key] = value
        end
    end

    return flat
end""",
        "category": "integration",
        "tags": ["json", "transform", "api", "data-mapping", "etl"]
    },
    {
        "description": "Redis cache operations",
        "code": """-- Create Redis command structure
function redis_command(cmd, ...)
    local args = {...}
    return {
        command = cmd,
        args = args,
        timestamp = os.time()
    }
end

-- SET operation with expiration
function redis_set(key, value, ttl)
    local cmd = {
        command = "SET",
        args = {key, value}
    }

    if ttl then
        table.insert(cmd.args, "EX")
        table.insert(cmd.args, tostring(ttl))
    end

    return cmd
end

-- Cache manager with TTL
function create_cache_manager(default_ttl)
    local manager = {
        default_ttl = default_ttl or 3600  -- 1 hour default
    }

    function manager:set(key, value, ttl)
        ttl = ttl or self.default_ttl
        return redis_set(key, value, ttl)
    end

    function manager:get(key)
        return redis_command("GET", key)
    end

    function manager:cache_key(prefix, id)
        return string.format("%s:%s", prefix, tostring(id))
    end

    return manager
end

-- Session storage
function create_session_store()
    local store = {}

    function store:save_session(session_id, user_data, ttl)
        local key = "session:" .. session_id
        local value = string.format(
            '{"user_id":%d,"username":"%s","created_at":%d}',
            user_data.user_id,
            user_data.username,
            os.time()
        )
        return redis_set(key, value, ttl or 1800)
    end

    return store
end""",
        "category": "integration",
        "tags": ["redis", "cache", "session", "key-value", "storage"]
    },
    {
        "description": "PostgreSQL query builder",
        "code": """-- Build SELECT query
function build_select(table_name, columns, where_clause, limit)
    local cols = columns and table.concat(columns, ", ") or "*"
    local query = string.format("SELECT %s FROM %s", cols, table_name)

    if where_clause then
        query = query .. " WHERE " .. where_clause
    end

    if limit then
        query = query .. " LIMIT " .. tostring(limit)
    end

    return query .. ";"
end

-- Build INSERT query
function build_insert(table_name, data)
    local columns = {}
    local values = {}

    for key, value in pairs(data) do
        table.insert(columns, key)
        if type(value) == "string" then
            table.insert(values, string.format("'%s'", value))
        elseif type(value) == "number" then
            table.insert(values, tostring(value))
        else
            table.insert(values, "NULL")
        end
    end

    return string.format(
        "INSERT INTO %s (%s) VALUES (%s);",
        table_name,
        table.concat(columns, ", "),
        table.concat(values, ", ")
    )
end

-- User repository pattern
function create_user_repository()
    local repo = {
        table_name = "users"
    }

    function repo:find_by_id(user_id)
        return build_select(self.table_name, nil, "id = " .. tostring(user_id), 1)
    end

    function repo:create(user_data)
        return build_insert(self.table_name, user_data)
    end

    return repo
end""",
        "category": "integration",
        "tags": ["postgresql", "sql", "database", "query-builder", "orm"]
    },
    {
        "description": "Event processor - Kafka to Database",
        "code": """-- Parse Kafka message from JSON
function parse_kafka_message(json_string)
    local message = {}
    message.topic = json_string:match('"topic":"([^"]+)"')
    message.key = json_string:match('"key":"([^"]+)"')
    local ts = json_string:match('"timestamp":(%d+)')
    message.timestamp = tonumber(ts)

    -- Extract value object
    local value_str = json_string:match('"value":%{(.-)%}')
    if value_str then
        message.value = {}
        for k, v in value_str:gmatch('"([^"]+)":"([^"]+)"') do
            message.value[k] = v
        end
    end

    return message
end

-- Process event and generate SQL
function process_user_event(event)
    local event_type = event.value.event_type
    local user_id = event.value.user_id
    local data = event.value.data

    if event_type == "user.created" then
        return build_insert("users", data)
    elseif event_type == "user.updated" then
        return build_update("users", data, "id = " .. user_id)
    elseif event_type == "user.deleted" then
        return build_delete("users", "id = " .. user_id)
    end

    return nil
end

-- Batch processing with error handling
function process_batch(messages, handler)
    local results = {
        processed = 0,
        failed = 0,
        errors = {}
    }

    for i, msg in ipairs(messages) do
        local success, result = pcall(function()
            return handler(msg)
        end)

        if success then
            results.processed = results.processed + 1
        else
            results.failed = results.failed + 1
            table.insert(results.errors, {
                index = i,
                error = result
            })
        end
    end

    return results
end""",
        "category": "integration",
        "tags": ["event-driven", "kafka", "database", "etl", "batch-processing"]
    }
]


# ============================================================
# LowCode Basic Rules and Patterns (MTS Octapi)
# ============================================================

LOWCODE_RULES = [
    {
        "description": "LowCode Rule 1: Accessing workflow variables. Use wf.vars to access workflow variables. Use wf.initVariables for initial variables. Example: wf.vars.emails, wf.vars.try_count_n, wf.initVariables.recallTime",
        "code": """-- Accessing workflow variables
-- wf.vars - runtime variables
local emails = wf.vars.emails
local counter = wf.vars.try_count_n

-- wf.initVariables - initial variables
local startTime = wf.initVariables.recallTime

-- Nested access
local result = wf.vars.RESTbody.result
local datum = wf.vars.json.IDOC.ZCDF_HEAD.DATUM""",
        "category": "lowcode",
        "tags": ["wf.vars", "wf.initVariables", "variables", "access", "basics"]
    },
    {
        "description": "LowCode Rule 2: Array operations. Use # operator for array length. Arrays are 1-indexed in Lua. Use ipairs() for iteration. Use _utils.array.new() to create new arrays. Use _utils.array.markAsArray(arr) to mark variable as array.",
        "code": """-- Array length
local length = #wf.vars.emails

-- Last element (arrays are 1-indexed)
local last = wf.vars.emails[#wf.vars.emails]

-- First element
local first = wf.vars.emails[1]

-- Iteration with ipairs
for i, email in ipairs(wf.vars.emails) do
    print(i, email)
end

-- Create new array
local newArray = _utils.array.new()

-- Mark existing variable as array
_utils.array.markAsArray(myVar)""",
        "category": "lowcode",
        "tags": ["array", "length", "indexing", "ipairs", "_utils.array", "iteration"]
    },
    {
        "description": "LowCode Rule 3: Table/Object operations. Use pairs() to iterate over tables. Use nil to delete keys. Check field existence with ~= nil. Access nested fields with dot notation.",
        "code": """-- Iterate over table
for key, value in pairs(wf.vars.RESTbody.result) do
    print(key, value)
end

-- Delete key by setting to nil
myTable.unwantedKey = nil

-- Check if field exists
if wf.vars.json.IDOC.ZCDF_HEAD.DATUM ~= nil then
    -- field exists
end

-- Nested access
local packages = wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES""",
        "category": "lowcode",
        "tags": ["table", "pairs", "nil", "object", "nested", "iteration"]
    },
    {
        "description": "LowCode Rule 4: Type checking and conversion. Use type() to check variable type. Use tonumber() to convert strings to numbers. Check for nil before operations. Handle both single values and arrays.",
        "code": """-- Type checking
if type(myVar) == "table" then
    -- it's a table/array
elseif type(myVar) == "string" then
    -- it's a string
end

-- String to number conversion
local num = tonumber("42")
local squared = num * num

-- Check for nil
if myVar ~= nil then
    -- safe to use
end

-- Ensure array (handle both single value and array)
function ensureArray(value)
    if type(value) ~= "table" then
        return {value}
    end
    return value
end""",
        "category": "lowcode",
        "tags": ["type", "tonumber", "nil", "conversion", "type_checking"]
    },
    {
        "description": "LowCode Rule 5: String operations. Use string.format() for formatting. Use string.sub() for substrings. Use .. for concatenation. Pattern matching with string.match().",
        "code": """-- String formatting (ISO 8601 example)
local datum = "20231015"
local time = "153000"
local year = string.sub(datum, 1, 4)
local month = string.sub(datum, 5, 6)
local day = string.sub(datum, 7, 8)
local hour = string.sub(time, 1, 2)
local min = string.sub(time, 3, 4)
local sec = string.sub(time, 5, 6)

local iso8601 = string.format("%s-%s-%sT%s:%s:%s+00:00",
    year, month, day, hour, min, sec)

-- Concatenation
local fullName = firstName .. " " .. lastName

-- Pattern matching
local year, month, day = iso_str:match("(%d+)-(%d+)-(%d+)T")""",
        "category": "lowcode",
        "tags": ["string", "format", "substring", "concatenation", "pattern_matching"]
    },
    {
        "description": "LowCode Rule 6: Filtering and mapping arrays. Create new array with _utils.array.new(). Use ipairs() to iterate. Check conditions and add matching elements. Common pattern: filter by field value.",
        "code": """-- Filter array by condition
local filtered = _utils.array.new()

for i, item in ipairs(wf.vars.parsedCsv) do
    -- Check if Discount or Markdown has value
    if (item.Discount and item.Discount ~= "") or
       (item.Markdown and item.Markdown ~= "") then
        filtered[#filtered + 1] = item
    end
end

return filtered""",
        "category": "lowcode",
        "tags": ["filter", "array", "ipairs", "_utils.array", "condition", "mapping"]
    },
    {
        "description": "LowCode Rule 7: Return statement. For LowCode scripts, use return to output result. Can return simple values, arrays, or tables. Return statement should be at the end of script.",
        "code": """-- Return simple value
return wf.vars.emails[#wf.vars.emails]

-- Return computed value
return wf.vars.try_count_n + 1

-- Return array
return filtered

-- Return table/object
return {
    timestamp = epoch_seconds,
    formatted = iso8601
}""",
        "category": "lowcode",
        "tags": ["return", "output", "result", "lowcode"]
    }
]


# ============================================================
# LowCode Examples from MTS Octapi Public Dataset (2026)
# ============================================================

LOWCODE_EXAMPLES = [
    {
        "description": "Задача 1: Последний элемент массива. Из полученного списка email получи последний. Контекст: wf.vars.emails = ['user1@example.com', 'user2@example.com', 'user3@example.com']. Ожидаемый результат: 'user3@example.com'",
        "code": """-- Задача: Из полученного списка email получи последний
-- Контекст: wf.vars.emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
-- Решение: используем оператор # для получения длины массива
return wf.vars.emails[#wf.vars.emails]""",
        "category": "lowcode",
        "tags": ["array", "wf.vars", "last_element", "indexing"]
    },
    {
        "description": "Задача 2: Счётчик попыток. Увеличивай значение переменной try_count_n на каждой итерации. Контекст: wf.vars.try_count_n = 3. Ожидаемый результат: 4",
        "code": """-- Задача: Увеличивай значение переменной try_count_n на каждой итерации
-- Контекст: wf.vars.try_count_n = 3
-- Решение: простое увеличение на 1
return wf.vars.try_count_n + 1""",
        "category": "lowcode",
        "tags": ["counter", "increment", "wf.vars", "arithmetic"]
    },
    {
        "description": "Задача 3: Очистка значений в переменных. Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL (оставь только эти поля, удали остальные). Контекст: wf.vars.RESTbody.result = [{ID: 123, ENTITY_ID: 456, CALL: 'example', OTHER_KEY_1: 'value1', OTHER_KEY_2: 'value2'}]. Ожидаемый результат: [{ID: 123, ENTITY_ID: 456, CALL: 'example'}]",
        "code": """-- Задача: Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL
-- Контекст: wf.vars.RESTbody.result содержит массив объектов с разными ключами
-- Решение: проходим по всем объектам и удаляем ключи, которые НЕ равны ID, ENTITY_ID, CALL
result = wf.vars.RESTbody.result

for _, filteredEntry in pairs(result) do
    for key, value in pairs(filteredEntry) do
        if key ~= "ID" and key ~= "ENTITY_ID" and key ~= "CALL" then
            filteredEntry[key] = nil
        end
    end
end

return result""",
        "category": "lowcode",
        "tags": ["filter", "object", "keys", "wf.vars", "REST", "pairs"]
    },
    {
        "description": "Задача 4: Приведение времени к ISO 8601. Преобразуй время из формата 'YYYYMMDD' и 'HHMMSS' в строку в формате ISO 8601. Контекст: wf.vars.json.IDOC.ZCDF_HEAD.DATUM = '20231015', TIME = '153000'. Ожидаемый результат: '2023-10-15T15:30:00.00000Z'",
        "code": """-- Задача: Преобразуй время из формата 'YYYYMMDD' и 'HHMMSS' в строку в формате ISO 8601
-- Контекст: wf.vars.json.IDOC.ZCDF_HEAD.DATUM = "20231015", TIME = "153000"
-- Решение: разбиваем строки на части и форматируем в ISO 8601
DATUM = wf.vars.json.IDOC.ZCDF_HEAD.DATUM
TIME = wf.vars.json.IDOC.ZCDF_HEAD.TIME

local function safe_sub(str, start, finish)
    local s = string.sub(str, start, math.min(finish, #str))
    return s ~= "" and s or "00"
end

year = safe_sub(DATUM, 1, 4)
month = safe_sub(DATUM, 5, 6)
day = safe_sub(DATUM, 7, 8)
hour = safe_sub(TIME, 1, 2)
minute = safe_sub(TIME, 3, 4)
second = safe_sub(TIME, 5, 6)

iso_date = string.format(
    '%s-%s-%sT%s:%s:%s.00000Z',
    year, month, day,
    hour, minute, second
)

return iso_date""",
        "category": "lowcode",
        "tags": ["date", "time", "ISO8601", "format", "string", "wf.vars"]
    },
    {
        "description": "Задача 5: Проверка типа данных. Преобразовать структуру данных так, чтобы все элементы items в ZCDF_PACKAGES всегда были представлены в виде массивов, даже если они изначально не являются массивами. Контекст: wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES = [{items: [{sku: 'A'}, {sku: 'B'}]}, {items: {sku: 'C'}}]. Ожидаемый результат: все items - массивы",
        "code": """-- Задача: Преобразовать структуру данных так, чтобы все элементы items в ZCDF_PACKAGES всегда были массивами
-- Контекст: items может быть объектом или массивом
-- Решение: проверяем тип и преобразуем объект в массив с одним элементом
function ensureArray(t)
    if type(t) ~= "table" then
        return {t}
    end
    local isArray = true
    for k, v in pairs(t) do
        if type(k) ~= "number" or math.floor(k) ~= k then
            isArray = false
            break
        end
    end
    return isArray and t or {t}
end

function ensureAllItemsAreArrays(objectsArray)
    if type(objectsArray) ~= "table" then
        return objectsArray
    end
    for _, obj in ipairs(objectsArray) do
        if type(obj) == "table" and obj.items then
            obj.items = ensureArray(obj.items)
        end
    end
    return objectsArray
end

return ensureAllItemsAreArrays(wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES)""",
        "category": "lowcode",
        "tags": ["type_check", "array", "ensure", "wf.vars", "ipairs"]
    },
    {
        "description": "Задача 6: Фильтрация элементов массива. Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown. Контекст: wf.vars.parsedCsv = [{SKU: 'A001', Discount: '10%', Markdown: ''}, {SKU: 'A002', Discount: '', Markdown: '5%'}, {SKU: 'A003', Discount: null, Markdown: null}]. Ожидаемый результат: только первые 2 элемента",
        "code": """-- Задача: Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown
-- Контекст: wf.vars.parsedCsv содержит массив объектов с полями SKU, Discount, Markdown
-- Решение: используем _utils.array.new() и фильтруем по условию
local result = _utils.array.new()
local items = wf.vars.parsedCsv

for _, item in ipairs(items) do
    if (item.Discount ~= "" and item.Discount ~= nil) or (item.Markdown ~= "" and item.Markdown ~= nil) then
        table.insert(result, item)
    end
end

return result""",
        "category": "lowcode",
        "tags": ["filter", "array", "wf.vars", "_utils.array", "ipairs"]
    },
    {
        "description": "Задача 7: Дополнение существующего кода. Добавь переменную с квадратом числа. Контекст: число '5' нужно преобразовать в число и вычислить квадрат. Ожидаемый результат: {num: 5, squared: 25}",
        "code": """-- Задача: Добавь переменную с квадратом числа
-- Контекст: работа с числами, преобразование строки в число
-- Решение: используем tonumber() для преобразования и возвращаем квадрат
local n = tonumber('5')
return n * n""",
        "category": "lowcode",
        "tags": ["variable", "tonumber", "arithmetic", "multiple_variables"]
    },
    {
        "description": "Задача 8: Конвертация времени в Unix. Конвертируй время в переменной recallTime в unix-формат. Контекст: wf.initVariables.recallTime = '2023-10-15T15:30:00+00:00'. Ожидаемый результат: 1697382600 (Unix timestamp)",
        "code": """-- Задача: Конвертируй время в переменной recallTime в unix-формат
-- Контекст: wf.initVariables.recallTime содержит время в формате ISO 8601
-- Решение: парсим ISO 8601 и вычисляем количество секунд с 1970-01-01
local iso_time = wf.initVariables.recallTime
local days_in_month = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}

if not iso_time or not iso_time:match("^%d%d%d%d%-%d%d%-%d%dT") then
    return nil
end

local function is_leap_year(year)
    return (year % 4 == 0 and year % 100 ~= 0) or (year % 400 == 0)
end

local function days_since_epoch(year, month, day)
    local days = 0
    for y = 1970, year - 1 do
        days = days + (is_leap_year(y) and 366 or 365)
    end
    for m = 1, month - 1 do
        days = days + days_in_month[m]
        if m == 2 and is_leap_year(year) then
            days = days + 1
        end
    end
    days = days + (day - 1)
    return days
end

local function parse_iso8601_to_epoch(iso_str)
    if not iso_str then
        error("Дата не задана (nil)")
    end

    local year, month, day, hour, min, sec, ms, offset_sign, offset_hour, offset_min =
        iso_str:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)%.(%d+)([+-])(%d+):(%d+)")

    if not year then
        year, month, day, hour, min, sec, offset_sign, offset_hour, offset_min =
            iso_str:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)([+-])(%d+):(%d+)")
        ms = 0
    end

    if not year then
        error("Невозможно разобрать дату: " .. tostring(iso_str))
    end

    year = tonumber(year)
    month = tonumber(month)
    day = tonumber(day)
    hour = tonumber(hour)
    min = tonumber(min)
    sec = tonumber(sec)
    ms = tonumber(ms) or 0
    offset_hour = tonumber(offset_hour)
    offset_min = tonumber(offset_min)

    local total_days = days_since_epoch(year, month, day)
    local total_seconds = total_days * 86400 + hour * 3600 + min * 60 + sec

    local offset_seconds = offset_hour * 3600 + offset_min * 60
    if offset_sign == "-" then
        offset_seconds = -offset_seconds
    end

    return total_seconds - offset_seconds
end

local epoch_seconds = parse_iso8601_to_epoch(iso_time)
return epoch_seconds""",
        "category": "lowcode",
        "tags": ["unix_timestamp", "date", "time", "wf.initVariables", "ISO8601", "parsing"]
    }
]


# ============================================================
# Initialization Functions
# ============================================================

def create_knowledge_base_documents() -> List[Document]:
    """
    Create all knowledge base documents.

    Returns:
        List of Document objects ready for RAG system
    """
    documents = []

    # Combine all example sets
    all_examples = (
        LUA_STDLIB_EXAMPLES +
        ALGORITHM_EXAMPLES +
        ADVANCED_ALGORITHM_EXAMPLES +
        PATTERN_EXAMPLES +
        DATA_STRUCTURE_EXAMPLES +
        BEST_PRACTICE_EXAMPLES +
        FILE_IO_EXAMPLES +
        METATABLE_EXAMPLES +
        COROUTINE_EXAMPLES +
        STRING_PROCESSING_EXAMPLES +
        TABLE_DATA_EXAMPLES +
        LOWCODE_RULES +             # NEW: LowCode basic rules and patterns
        LOWCODE_PATTERN_EXAMPLES +  # MTS Octapi public tasks
        LOWCODE_BEST_PRACTICES +    # LowCode best practices
        LOWCODE_EXAMPLES +          # NEW: MTS Octapi 8 examples from PDF
        LOWCODE_INTEGRATION_EXAMPLES +  # Original low-code patterns
        INTEGRATION_EXAMPLES  # MTS Hackathon 2026 - Integration patterns
    )

    for example in all_examples:
        content = f"{example['description']}\n\n```lua\n{example['code']}\n```"

        metadata = {
            "category": example["category"],
            "tags": ",".join(example.get("tags", [])),
            "type": "code_example"
        }

        doc = Document(
            page_content=content,
            metadata=metadata
        )

        documents.append(doc)

    logger.info(f"Created {len(documents)} knowledge base documents")
    return documents


def initialize_rag_with_examples(rag_system) -> None:
    """
    Initialize RAG system with all code examples.

    Args:
        rag_system: RAGSystem instance
    """
    logger.info("Initializing RAG knowledge base...")

    # Check if already initialized
    stats = rag_system.get_stats()
    if stats["total_documents"] > 0:
        logger.info(f"Knowledge base already has {stats['total_documents']} documents, skipping initialization")
        return

    # Add all examples
    documents = create_knowledge_base_documents()
    rag_system.add_documents(documents)

    logger.info(f"Knowledge base initialized with {len(documents)} examples")
