-- Kafka Consumer Pattern
-- Processes messages from Kafka topics
-- Use case: Event processing, stream processing, message queue consumption

-- Parse Kafka message from JSON-like string
function parse_kafka_message(json_string)
    -- Simple JSON parser for Kafka message structure
    local message = {}

    -- Extract topic
    message.topic = json_string:match('"topic":"([^"]+)"')

    -- Extract key
    message.key = json_string:match('"key":"([^"]+)"')

    -- Extract timestamp
    local ts = json_string:match('"timestamp":(%d+)')
    message.timestamp = tonumber(ts)

    -- Extract value object
    local value_str = json_string:match('"value":%{(.-)%}')
    if value_str then
        message.value = {}
        for k, v in value_str:gmatch('"([^"]+)":"([^"]+)"') do
            message.value[k] = v
        end
        for k, v in value_str:gmatch('"([^"]+)":(%d+)') do
            message.value[k] = tonumber(v)
        end
    end

    return message
end

-- Process message with error handling
function process_message(message, handler)
    local success, result = pcall(function()
        return handler(message)
    end)

    if success then
        return {
            status = "success",
            result = result,
            message_key = message.key
        }
    else
        return {
            status = "error",
            error = result,
            message_key = message.key
        }
    end
end

-- Batch message processing
function process_batch(messages, handler)
    local results = {
        processed = 0,
        failed = 0,
        errors = {}
    }

    for i, msg in ipairs(messages) do
        local result = process_message(msg, handler)
        if result.status == "success" then
            results.processed = results.processed + 1
        else
            results.failed = results.failed + 1
            table.insert(results.errors, {
                index = i,
                key = msg.key,
                error = result.error
            })
        end
    end

    return results
end

-- Filter messages by criteria
function filter_messages(messages, predicate)
    local filtered = {}
    for i, msg in ipairs(messages) do
        if predicate(msg) then
            table.insert(filtered, msg)
        end
    end
    return filtered
end

-- Example usage:
-- local handler = function(msg)
--     print("Processing:", msg.value.phone)
--     return true
-- end
-- local result = process_message(parsed_msg, handler)
