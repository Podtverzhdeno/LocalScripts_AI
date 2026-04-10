-- Merge Sort Implementation in Lua

local function mergeSort(arr, left, right)
    if left >= right then
        return
    end

    local mid = math.floor((left + right) / 2)
    mergeSort(arr, left, mid)
    mergeSort(arr, mid + 1, right)

    local merged = {}
    local i, j = left, mid + 1
    while i <= mid and j <= right do
        if arr[i] <= arr[j] then
            table.insert(merged, arr[i])
            i = i + 1
        else
            table.insert(merged, arr[j])
            j = j + 1
        end
    end

    while i <= mid do
        table.insert(merged, arr[i])
        i = i + 1
    end

    while j <= right do
        table.insert(merged, arr[j])
        j = j + 1
    end

    for k = 0, #merged - 1 do
        arr[left + k] = merged[k + 1]
    end
end

local function isValidArray(arr)
    if type(arr) ~= "table" or #arr == 0 then
        return false
    end
    for _, v in ipairs(arr) do
        if type(v) ~= "number" then
            return false
        end
    end
    return true
end

local function sort(arr)
    if not isValidArray(arr) then
        error("Input must be a non-empty table of numbers.")
    end
    mergeSort(arr, 1, #arr)
end

-- Example usage
local data = {38, 27, 43, 3, 9, 82, 10}
sort(data)
for _, v in ipairs(data) do
    print(v)
end