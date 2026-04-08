-- CRUD operations for in-memory table data (Excel/CSV alternative)
-- Tags: crud, table, data, excel, csv, database

local TableCRUD = {}

-- Sample data structure (like Excel sheet)
local data = {
    {"ID", "Name", "Age", "City"},  -- Header row at index 1
    {1, "Alice", 30, "New York"},
    {2, "Bob", 25, "Los Angeles"},
    {3, "Charlie", 35, "Chicago"}
}

-- CREATE: Add new row to table
function TableCRUD.create(tbl, row)
    table.insert(tbl, row)
    return #tbl - 1  -- Return new row count (excluding header)
end

-- READ: Find rows matching criteria
function TableCRUD.read(tbl, col_index, value)
    local results = {}
    for i = 2, #tbl do  -- Skip header at index 1
        if tbl[i][col_index] == value then
            table.insert(results, tbl[i])
        end
    end
    return results
end

-- READ ALL: Get all data rows (excluding header)
function TableCRUD.readAll(tbl)
    local results = {}
    for i = 2, #tbl do
        table.insert(results, tbl[i])
    end
    return results
end

-- UPDATE: Modify existing row by ID
function TableCRUD.update(tbl, id, new_data)
    for i = 2, #tbl do
        if tbl[i][1] == id then  -- Assuming ID is first column
            tbl[i] = new_data
            return true
        end
    end
    return false
end

-- DELETE: Remove row by ID
function TableCRUD.delete(tbl, id)
    for i = 2, #tbl do
        if tbl[i][1] == id then
            table.remove(tbl, i)
            return true
        end
    end
    return false
end

-- FILTER: Get rows matching condition
function TableCRUD.filter(tbl, predicate)
    local results = {}
    for i = 2, #tbl do
        if predicate(tbl[i]) then
            table.insert(results, tbl[i])
        end
    end
    return results
end

-- Helper: Print table in readable format
function TableCRUD.print(tbl)
    for i, row in ipairs(tbl) do
        local line = ""
        for j, cell in ipairs(row) do
            line = line .. tostring(cell) .. "\t"
        end
        print(line)
    end
end

-- Example usage
print("=== Initial Data ===")
TableCRUD.print(data)

-- CREATE
print("\n=== CREATE ===")
TableCRUD.create(data, {4, "Diana", 28, "Houston"})
print("Added Diana, total rows:", #data - 1)

-- READ
print("\n=== READ ===")
local found = TableCRUD.read(data, 2, "Alice")  -- Find by Name column
print("Found", #found, "row(s) with Name='Alice'")

-- UPDATE
print("\n=== UPDATE ===")
TableCRUD.update(data, 2, {2, "Bob", 26, "San Francisco"})
print("Updated Bob's age and city")

-- DELETE
print("\n=== DELETE ===")
TableCRUD.delete(data, 3)
print("Deleted Charlie, total rows:", #data - 1)

-- FILTER
print("\n=== FILTER (Age >= 28) ===")
local adults = TableCRUD.filter(data, function(row)
    return row[3] >= 28  -- Age column
end)
print("Found", #adults, "row(s)")
TableCRUD.print({data[1], table.unpack(adults)})  -- Print with header

print("\n=== Final Data ===")
TableCRUD.print(data)
