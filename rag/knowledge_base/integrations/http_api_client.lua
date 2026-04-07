-- HTTP REST API Client Pattern
-- Makes HTTP requests to REST APIs with proper error handling
-- Use case: Microservices integration, external API calls, webhooks

-- Create HTTP request structure
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

-- Parse URL into components
function parse_url(url)
    local protocol, host, port, path = url:match("^(https?)://([^:/]+):?(%d*)(.*)$")
    return {
        protocol = protocol or "http",
        host = host,
        port = tonumber(port) or (protocol == "https" and 443 or 80),
        path = path ~= "" and path or "/"
    }
end

-- Build query string from table
function build_query_string(params)
    if not params or next(params) == nil then
        return ""
    end

    local parts = {}
    for key, value in pairs(params) do
        table.insert(parts, string.format("%s=%s", key, tostring(value)))
    end
    return "?" .. table.concat(parts, "&")
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

    -- Delete user
    function client:delete_user(user_id)
        local url = self.base_url .. "/users/" .. tostring(user_id)
        return create_http_request("DELETE", url)
    end

    -- List users with pagination
    function client:list_users(page, limit)
        local params = {page = page or 1, limit = limit or 10}
        local url = self.base_url .. "/users" .. build_query_string(params)
        return create_http_request("GET", url)
    end

    return client
end

-- Response parser
function parse_json_response(response_body)
    -- Simple JSON parser for common response structures
    local data = {}

    -- Extract id
    local id = response_body:match('"id":(%d+)')
    if id then data.id = tonumber(id) end

    -- Extract string fields
    for key, value in response_body:gmatch('"([^"]+)":"([^"]+)"') do
        data[key] = value
    end

    return data
end

-- Example usage:
-- local client = create_user_api_client("https://api.example.com")
-- local request = client:get_user(123)
-- print(request.method, request.url)
