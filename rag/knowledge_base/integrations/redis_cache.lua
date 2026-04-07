-- Redis Cache Pattern
-- Interacts with Redis for caching and data storage
-- Use case: Session storage, rate limiting, temporary data, cache layer

-- Create Redis command structure
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

-- GET operation
function redis_get(key)
    return redis_command("GET", key)
end

-- DELETE operation
function redis_del(key)
    return redis_command("DEL", key)
end

-- Hash operations
function redis_hset(hash_key, field, value)
    return redis_command("HSET", hash_key, field, value)
end

function redis_hget(hash_key, field)
    return redis_command("HGET", hash_key, field)
end

function redis_hgetall(hash_key)
    return redis_command("HGETALL", hash_key)
end

-- List operations
function redis_lpush(list_key, value)
    return redis_command("LPUSH", list_key, value)
end

function redis_rpush(list_key, value)
    return redis_command("RPUSH", list_key, value)
end

function redis_lpop(list_key)
    return redis_command("LPOP", list_key)
end

function redis_lrange(list_key, start, stop)
    return redis_command("LRANGE", list_key, tostring(start), tostring(stop))
end

-- Cache wrapper with TTL
function create_cache_manager(default_ttl)
    local manager = {
        default_ttl = default_ttl or 3600  -- 1 hour default
    }

    function manager:set(key, value, ttl)
        ttl = ttl or self.default_ttl
        return redis_set(key, value, ttl)
    end

    function manager:get(key)
        return redis_get(key)
    end

    function manager:delete(key)
        return redis_del(key)
    end

    -- Cache with prefix
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
        return redis_set(key, value, ttl or 1800)  -- 30 min default
    end

    function store:get_session(session_id)
        local key = "session:" .. session_id
        return redis_get(key)
    end

    function store:delete_session(session_id)
        local key = "session:" .. session_id
        return redis_del(key)
    end

    return store
end

-- Rate limiter
function create_rate_limiter(max_requests, window_seconds)
    local limiter = {
        max_requests = max_requests,
        window = window_seconds
    }

    function limiter:check(user_id)
        local key = string.format("rate_limit:%s:%d", user_id, os.time() // self.window)
        return redis_command("INCR", key)
    end

    function limiter:is_allowed(current_count)
        return current_count <= self.max_requests
    end

    return limiter
end

-- Example usage:
-- local cache = create_cache_manager(3600)
-- local set_cmd = cache:set("user:123", '{"name":"John"}', 7200)
-- local get_cmd = cache:get("user:123")
