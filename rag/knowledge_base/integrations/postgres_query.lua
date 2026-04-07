-- PostgreSQL Query Pattern
-- Builds SQL queries for PostgreSQL database operations
-- Use case: Database integration, CRUD operations, data persistence

-- Build SELECT query
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
        elseif value == nil then
            table.insert(values, "NULL")
        else
            table.insert(values, string.format("'%s'", tostring(value)))
        end
    end

    return string.format(
        "INSERT INTO %s (%s) VALUES (%s);",
        table_name,
        table.concat(columns, ", "),
        table.concat(values, ", ")
    )
end

-- Build UPDATE query
function build_update(table_name, data, where_clause)
    local set_parts = {}

    for key, value in pairs(data) do
        local value_str
        if type(value) == "string" then
            value_str = string.format("'%s'", value)
        elseif type(value) == "number" then
            value_str = tostring(value)
        else
            value_str = "NULL"
        end
        table.insert(set_parts, string.format("%s = %s", key, value_str))
    end

    local query = string.format("UPDATE %s SET %s", table_name, table.concat(set_parts, ", "))

    if where_clause then
        query = query .. " WHERE " .. where_clause
    end

    return query .. ";"
end

-- Build DELETE query
function build_delete(table_name, where_clause)
    local query = string.format("DELETE FROM %s", table_name)

    if where_clause then
        query = query .. " WHERE " .. where_clause
    end

    return query .. ";"
end

-- WHERE clause builder
function build_where(conditions)
    local parts = {}

    for key, value in pairs(conditions) do
        if type(value) == "string" then
            table.insert(parts, string.format("%s = '%s'", key, value))
        elseif type(value) == "number" then
            table.insert(parts, string.format("%s = %s", key, tostring(value)))
        elseif type(value) == "table" then
            -- Handle operators: {operator = ">=", value = 18}
            if value.operator and value.value then
                table.insert(parts, string.format("%s %s %s", key, value.operator, tostring(value.value)))
            end
        end
    end

    return table.concat(parts, " AND ")
end

-- User repository pattern
function create_user_repository()
    local repo = {
        table_name = "users"
    }

    function repo:find_by_id(user_id)
        return build_select(self.table_name, nil, "id = " .. tostring(user_id), 1)
    end

    function repo:find_by_email(email)
        return build_select(self.table_name, nil, string.format("email = '%s'", email), 1)
    end

    function repo:create(user_data)
        return build_insert(self.table_name, user_data)
    end

    function repo:update(user_id, user_data)
        return build_update(self.table_name, user_data, "id = " .. tostring(user_id))
    end

    function repo:delete(user_id)
        return build_delete(self.table_name, "id = " .. tostring(user_id))
    end

    function repo:list_all(limit)
        return build_select(self.table_name, nil, nil, limit)
    end

    function repo:find_by_role(role, limit)
        return build_select(self.table_name, nil, string.format("role = '%s'", role), limit)
    end

    return repo
end

-- Transaction builder
function build_transaction(queries)
    local parts = {"BEGIN;"}

    for _, query in ipairs(queries) do
        table.insert(parts, query)
    end

    table.insert(parts, "COMMIT;")

    return table.concat(parts, "\n")
end

-- Example usage:
-- local repo = create_user_repository()
-- local query = repo:find_by_email("user@example.com")
-- print(query)  -- SELECT * FROM users WHERE email = 'user@example.com' LIMIT 1;
--
-- local insert = repo:create({name = "John", email = "john@example.com", role = "admin"})
-- print(insert)  -- INSERT INTO users (name, email, role) VALUES ('John', 'john@example.com', 'admin');
