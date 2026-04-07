-- Kafka Producer Pattern
-- Sends messages to Kafka topics with proper formatting
-- Use case: Event streaming, microservices communication, data pipelines

-- Format phone number for Kafka message
function format_phone_for_kafka(phone)
    -- Remove all non-digit characters
    local normalized = phone:gsub("[^%d]", "")

    -- Ensure it starts with country code
    if #normalized == 10 then
        normalized = "7" .. normalized  -- Add Russia country code
    end

    return {
        topic = "phone_numbers",
        key = normalized,
        value = {
            phone = normalized,
            original = phone,
            timestamp = os.time(),
            source = "lua_integration"
        }
    }
end

-- Generic Kafka message formatter
function create_kafka_message(topic, key, data)
    return {
        topic = topic,
        key = key or "",
        value = data,
        timestamp = os.time(),
        headers = {
            ["content-type"] = "application/json",
            ["producer"] = "localscript"
        }
    }
end

-- Batch message creation
function create_kafka_batch(topic, records)
    local batch = {}
    for i, record in ipairs(records) do
        batch[i] = create_kafka_message(topic, record.key, record.data)
    end
    return batch
end

-- Serialize message to JSON-like string
function serialize_kafka_message(message)
    local parts = {}
    table.insert(parts, string.format('"topic":"%s"', message.topic))
    table.insert(parts, string.format('"key":"%s"', message.key))
    table.insert(parts, string.format('"timestamp":%d', message.timestamp))

    -- Serialize value
    if type(message.value) == "table" then
        local value_parts = {}
        for k, v in pairs(message.value) do
            if type(v) == "string" then
                table.insert(value_parts, string.format('"%s":"%s"', k, v))
            else
                table.insert(value_parts, string.format('"%s":%s', k, tostring(v)))
            end
        end
        table.insert(parts, string.format('"value":{%s}', table.concat(value_parts, ",")))
    end

    return "{" .. table.concat(parts, ",") .. "}"
end

-- Example usage:
-- local msg = format_phone_for_kafka("+7 (999) 123-45-67")
-- print(serialize_kafka_message(msg))
-- Output: {"topic":"phone_numbers","key":"79991234567","timestamp":...,"value":{...}}
