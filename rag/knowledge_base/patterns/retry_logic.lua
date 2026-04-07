-- Retry Logic with Exponential Backoff Pattern
-- Implements retry mechanism with exponential backoff for transient failures
-- Use case: API calls, database connections, network requests

-- Retry configuration
local RetryConfig = {
    max_attempts = 3,
    initial_delay = 1,      -- seconds
    max_delay = 60,         -- seconds
    backoff_factor = 2,
    jitter = true
}

-- Execute function with retry logic
function retry_with_backoff(func, config)
    config = config or RetryConfig
    local attempts = 0
    local delay = config.initial_delay

    while attempts < config.max_attempts do
        attempts = attempts + 1

        -- Try to execute function
        local success, result = pcall(func)

        if success then
            return result, nil
        end

        -- Last attempt failed
        if attempts >= config.max_attempts then
            return nil, string.format("Failed after %d attempts: %s", attempts, result)
        end

        -- Calculate backoff delay
        local wait_time = math.min(delay, config.max_delay)

        -- Add jitter to prevent thundering herd
        if config.jitter then
            wait_time = wait_time * (0.5 + math.random() * 0.5)
        end

        print(string.format("Attempt %d failed, retrying in %.2f seconds...", attempts, wait_time))

        -- Wait before retry (in real implementation, use proper sleep)
        local start = os.time()
        while os.time() - start < wait_time do
            -- Busy wait (replace with proper sleep in production)
        end

        -- Exponential backoff
        delay = delay * config.backoff_factor
    end
end

-- Retry with custom predicate (retry only on specific errors)
function retry_if(func, should_retry, config)
    config = config or RetryConfig
    local attempts = 0
    local delay = config.initial_delay

    while attempts < config.max_attempts do
        attempts = attempts + 1

        local success, result = pcall(func)

        if success then
            return result, nil
        end

        -- Check if we should retry this error
        if not should_retry(result) then
            return nil, string.format("Non-retryable error: %s", result)
        end

        if attempts >= config.max_attempts then
            return nil, string.format("Failed after %d attempts: %s", attempts, result)
        end

        local wait_time = math.min(delay, config.max_delay)
        if config.jitter then
            wait_time = wait_time * (0.5 + math.random() * 0.5)
        end

        local start = os.time()
        while os.time() - start < wait_time do end

        delay = delay * config.backoff_factor
    end
end

-- Example usage:
-- local function unreliable_api_call()
--     if math.random() > 0.7 then
--         return {status = "success", data = "result"}
--     else
--         error("Connection timeout")
--     end
-- end
--
-- local result, err = retry_with_backoff(unreliable_api_call, {
--     max_attempts = 5,
--     initial_delay = 1,
--     backoff_factor = 2,
--     jitter = true
-- })
--
-- if result then
--     print("Success:", result.data)
-- else
--     print("Failed:", err)
-- end
