function reverse_string(str)
    local reversed = ""
    for i = #str, 1, -1 do
        reversed = reversed .. str:sub(i, i)
    end
    return reversed
end

-- Example usage:
print(reverse_string("Hello, World!"))  -- Output: !dlroW ,olleH
