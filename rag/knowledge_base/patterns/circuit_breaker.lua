-- Circuit Breaker Pattern
-- Prevents cascading failures by stopping requests to failing services
-- Use case: Microservices resilience, API fault tolerance, system stability

-- Circuit breaker states
local State = {
    CLOSED = "CLOSED",      -- Normal operation
    OPEN = "OPEN",          -- Blocking requests
    HALF_OPEN = "HALF_OPEN" -- Testing if service recovered
}

-- Circuit breaker class
local CircuitBreaker = {}
CircuitBreaker.__index = CircuitBreaker

function CircuitBreaker.new(config)
    local self = setmetatable({}, CircuitBreaker)

    -- Configuration
    self.failure_threshold = config.failure_threshold or 5
    self.success_threshold = config.success_threshold or 2
    self.timeout = config.timeout or 60  -- seconds
    self.half_open_max_calls = config.half_open_max_calls or 1

    -- State
    self.state = State.CLOSED
    self.failure_count = 0
    self.success_count = 0
    self.last_failure_time = 0
    self.half_open_calls = 0

    return self
end

-- Execute function through circuit breaker
function CircuitBreaker:call(func)
    -- Check if circuit should transition from OPEN to HALF_OPEN
    if self.state == State.OPEN then
        if os.time() - self.last_failure_time >= self.timeout then
            self.state = State.HALF_OPEN
            self.half_open_calls = 0
            print("Circuit breaker: OPEN -> HALF_OPEN")
        else
            return nil, "Circuit breaker is OPEN"
        end
    end

    -- Limit calls in HALF_OPEN state
    if self.state == State.HALF_OPEN then
        if self.half_open_calls >= self.half_open_max_calls then
            return nil, "Circuit breaker is HALF_OPEN (max calls reached)"
        end
        self.half_open_calls = self.half_open_calls + 1
    end

    -- Execute function
    local success, result = pcall(func)

    if success then
        self:on_success()
        return result, nil
    else
        self:on_failure()
        return nil, result
    end
end

-- Handle successful call
function CircuitBreaker:on_success()
    self.failure_count = 0

    if self.state == State.HALF_OPEN then
        self.success_count = self.success_count + 1

        if self.success_count >= self.success_threshold then
            self.state = State.CLOSED
            self.success_count = 0
            print("Circuit breaker: HALF_OPEN -> CLOSED")
        end
    end
end

-- Handle failed call
function CircuitBreaker:on_failure()
    self.failure_count = self.failure_count + 1
    self.last_failure_time = os.time()
    self.success_count = 0

    if self.state == State.HALF_OPEN then
        self.state = State.OPEN
        print("Circuit breaker: HALF_OPEN -> OPEN")
    elseif self.state == State.CLOSED then
        if self.failure_count >= self.failure_threshold then
            self.state = State.OPEN
            print("Circuit breaker: CLOSED -> OPEN")
        end
    end
end

-- Get current state
function CircuitBreaker:get_state()
    return self.state
end

-- Reset circuit breaker
function CircuitBreaker:reset()
    self.state = State.CLOSED
    self.failure_count = 0
    self.success_count = 0
    self.half_open_calls = 0
end

-- Example usage:
-- local breaker = CircuitBreaker.new({
--     failure_threshold = 3,
--     success_threshold = 2,
--     timeout = 10
-- })
--
-- local function unreliable_service()
--     if math.random() > 0.5 then
--         return "Success"
--     else
--         error("Service unavailable")
--     end
-- end
--
-- for i = 1, 10 do
--     local result, err = breaker:call(unreliable_service)
--     if result then
--         print(i, "Success:", result)
--     else
--         print(i, "Failed:", err)
--     end
-- end
