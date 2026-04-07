-- Email Validation Pattern
-- Validates email addresses according to RFC 5322 simplified rules
-- Use case: Form validation, user input sanitization, data quality checks

function validate_email(email)
    if type(email) ~= "string" then
        return false
    end

    -- Check basic structure: local@domain
    local pattern = "^[%w%._%+%-]+@[%w%.%-]+%.%w+$"
    if not string.match(email, pattern) then
        return false
    end

    -- Additional checks
    local local_part, domain = email:match("^(.+)@(.+)$")

    -- Local part should not start or end with dot
    if local_part:match("^%.") or local_part:match("%.$") then
        return false
    end

    -- No consecutive dots
    if local_part:match("%.%.") then
        return false
    end

    -- Domain should have at least one dot
    if not domain:match("%.") then
        return false
    end

    return true
end

-- Batch validation for multiple emails
function validate_emails(email_list)
    local results = {}
    for i, email in ipairs(email_list) do
        results[i] = {
            email = email,
            valid = validate_email(email)
        }
    end
    return results
end

-- Extract email from text
function extract_email(text)
    local pattern = "[%w%._%+%-]+@[%w%.%-]+%.%w+"
    return string.match(text, pattern)
end

-- Example usage:
-- print(validate_email("user@example.com"))  -- true
-- print(validate_email("invalid.email"))     -- false
-- print(validate_email("user+tag@domain.co.uk"))  -- true
