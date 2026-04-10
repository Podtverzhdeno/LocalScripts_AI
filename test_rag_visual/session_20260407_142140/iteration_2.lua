-- Merge sort implementation in Lua

local function merge_sort(arr)
    if type(arr) ~= "table" then
        error("Input must be a table")
    end

    local n = #arr
    if n <= 1 then
        return arr
    end

    local mid = math.floor(n / 2)
    local left_half = merge_sort({table.unpack(arr, 1, mid)})
    local right_half = merge_sort({table.unpack(arr, mid + 1, n)})

    local result = {}
    local i, j, k = 1, 1, 1

    while i <= #left_half and j <= #right_half do
        if left_half[i] <= right_half[j] then
            result[k] = left_half[i]
            i = i + 1
        else
            result[k] = right_half[j]
            j = j + 1
        end
        k = k + 1
    end

    while i <= #left_half do
        result[k] = left_half[i]
        i = i + 1
        k = k + 1
    end

    while j <= #right_half do
        result[k] = right_half[j]
        j = j + 1
        k = k + 1
    end

    return result
end

-- Example usage
local test_array = {38, 27, 43, 3, 9, 82, 10}
local sorted_array = merge_sort(test_array)

for _, v in ipairs(sorted_array) do
    print(v)
end