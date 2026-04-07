-- JSON Data Transformer Pattern
-- Transforms JSON structures between different API formats
-- Use case: API integration, data migration, format conversion

-- Transform user object from API A to API B format
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

    -- Extract top-level fields
    for key, value in nested_json:gmatch('"([^"]+)":"([^"]+)"') do
        if key ~= "user" then
            flat[key] = value
        end
    end

    return flat
end

-- Build nested structure from flat
function nest_json(flat_data, nest_key, nest_fields)
    local result = {}
    local nested = {}

    for key, value in pairs(flat_data) do
        local is_nested = false
        for _, field in ipairs(nest_fields) do
            if key == field then
                nested[key] = value
                is_nested = true
                break
            end
        end
        if not is_nested then
            result[key] = value
        end
    end

    result[nest_key] = nested
    return result
end

-- Serialize table to JSON string
function table_to_json(tbl, indent)
    indent = indent or 0
    local parts = {}
    local spacing = string.rep("  ", indent)

    for key, value in pairs(tbl) do
        local key_str = string.format('"%s"', key)
        local value_str

        if type(value) == "table" then
            value_str = table_to_json(value, indent + 1)
        elseif type(value) == "string" then
            value_str = string.format('"%s"', value)
        else
            value_str = tostring(value)
        end

        table.insert(parts, string.format('%s%s:%s', spacing, key_str, value_str))
    end

    return "{\n" .. table.concat(parts, ",\n") .. "\n" .. string.rep("  ", indent - 1) .. "}"
end

-- Array transformation
function transform_array(json_array, transformer)
    local items = {}
    local array_content = json_array:match('%[(.-)%]')

    if not array_content then
        return "[]"
    end

    -- Split by objects
    for item in array_content:gmatch('%{.-%}') do
        table.insert(items, transformer(item))
    end

    return "[" .. table.concat(items, ",") .. "]"
end

-- Example usage:
-- local source = '{"user":{"name":"John","email":"john@example.com"}}'
-- local target = transform_user_format(source)
-- print(target)  -- {"fullName":"John","contact":{"email":"john@example.com",...}}
