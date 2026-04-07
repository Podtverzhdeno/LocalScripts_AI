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
        TABLE_DATA_EXAMPLES
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
