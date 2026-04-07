-- Rate Limiter Pattern
-- Controls request rate to prevent system overload
-- Use case: API throttling, resource protection, DDoS prevention

-- Token bucket rate limiter
local TokenBucket = {}
TokenBucket.__index = TokenBucket

function TokenBucket.new(capacity, refill_rate)
    local self = setmetatable({}, TokenBucket)
    self.capacity = capacity           -- Maximum tokens
    self.tokens = capacity             -- Current tokens
    self.refill_rate = refill_rate     -- Tokens per second
    self.last_refill = os.time()
    return self
end

-- Try to consume tokens
function TokenBucket:consume(tokens)
    tokens = tokens or 1
    self:refill()

    if self.tokens >= tokens then
        self.tokens = self.tokens - tokens
        return true
    end

    return false
end

-- Refill tokens based on time elapsed
function TokenBucket:refill()
    local now = os.time()
    local elapsed = now - self.last_refill

    if elapsed > 0 then
        local new_tokens = elapsed * self.refill_rate
        self.tokens = math.min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    end
end

-- Get available tokens
function TokenBucket:available()
    self:refill()
    return self.tokens
end

-- Sliding window rate limiter
local SlidingWindow = {}
SlidingWindow.__index = SlidingWindow

function SlidingWindow.new(max_requests, window_seconds)
    local self = setmetatable({}, SlidingWindow)
    self.max_requests = max_requests
    self.window_seconds = window_seconds
    self.requests = {}
    return self
end

-- Try to allow request
function SlidingWindow:allow(user_id)
    local now = os.time()
    local window_start = now - self.window_seconds

    -- Initialize user's request history
    if not self.requests[user_id] then
        self.requests[user_id] = {}
    end

    -- Remove old requests outside window
    local user_requests = self.requests[user_id]
    local valid_requests = {}

    for _, timestamp in ipairs(user_requests) do
        if timestamp > window_start then
            table.insert(valid_requests, timestamp)
        end
    end

    self.requests[user_id] = valid_requests

    -- Check if under limit
    if #valid_requests < self.max_requests then
        table.insert(self.requests[user_id], now)
        return true, self.max_requests - #valid_requests - 1
    end

    -- Calculate retry after
    local oldest = valid_requests[1]
    local retry_after = oldest + self.window_seconds - now

    return false, 0, retry_after
end

-- Fixed window rate limiter
local FixedWindow = {}
FixedWindow.__index = FixedWindow

function FixedWindow.new(max_requests, window_seconds)
    local self = setmetatable({}, FixedWindow)
    self.max_requests = max_requests
    self.window_seconds = window_seconds
    self.windows = {}
    return self
end

-- Try to allow request
function FixedWindow:allow(user_id)
    local now = os.time()
    local window_key = math.floor(now / self.window_seconds)

    if not self.windows[user_id] then
        self.windows[user_id] = {}
    end

    local user_windows = self.windows[user_id]

    -- Clean old windows
    for key, _ in pairs(user_windows) do
        if key < window_key then
            user_windows[key] = nil
        end
    end

    -- Check current window
    local count = user_windows[window_key] or 0

    if count < self.max_requests then
        user_windows[window_key] = count + 1
        return true, self.max_requests - count - 1
    end

    return false, 0
end

-- Example usage:
-- Token bucket (100 requests, refill 10/sec)
-- local limiter = TokenBucket.new(100, 10)
-- if limiter:consume(1) then
--     print("Request allowed")
-- else
--     print("Rate limit exceeded")
-- end
--
-- Sliding window (10 requests per 60 seconds)
-- local limiter = SlidingWindow.new(10, 60)
-- local allowed, remaining, retry_after = limiter:allow("user_123")
-- if allowed then
--     print("Request allowed, remaining:", remaining)
-- else
--     print("Rate limited, retry after:", retry_after, "seconds")
-- end
