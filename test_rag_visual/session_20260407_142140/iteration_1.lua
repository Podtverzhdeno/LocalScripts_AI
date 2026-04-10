local function merge(left, right)
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
print(table.concat(sorted, ", "))