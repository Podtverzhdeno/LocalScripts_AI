-- Event-Driven Architecture Pattern
-- Implements event emitter/listener pattern for decoupled components
-- Use case: Microservices communication, plugin systems, reactive programming

-- Event emitter class
local EventEmitter = {}
EventEmitter.__index = EventEmitter

function EventEmitter.new()
    local self = setmetatable({}, EventEmitter)
    self.listeners = {}
    return self
end

-- Register event listener
function EventEmitter:on(event, callback)
    if not self.listeners[event] then
        self.listeners[event] = {}
    end
    table.insert(self.listeners[event], callback)
end

-- Remove event listener
function EventEmitter:off(event, callback)
    if not self.listeners[event] then return end

    for i, cb in ipairs(self.listeners[event]) do
        if cb == callback then
            table.remove(self.listeners[event], i)
            break
        end
    end
end

-- Emit event to all listeners
function EventEmitter:emit(event, ...)
    if not self.listeners[event] then return end

    for _, callback in ipairs(self.listeners[event]) do
        local success, err = pcall(callback, ...)
        if not success then
            print(string.format("Error in event handler for '%s': %s", event, err))
        end
    end
end

-- Once - listen to event only once
function EventEmitter:once(event, callback)
    local wrapper
    wrapper = function(...)
        callback(...)
        self:off(event, wrapper)
    end
    self:on(event, wrapper)
end

-- Example usage:
-- local emitter = EventEmitter.new()
--
-- emitter:on("user.created", function(user)
--     print("User created:", user.name)
-- end)
--
-- emitter:on("user.created", function(user)
--     print("Send welcome email to:", user.email)
-- end)
--
-- emitter:emit("user.created", {name = "John", email = "john@example.com"})
