-- Задача: Конвертируй время в переменной recallTime в unix-формат
-- Контекст: wf.initVariables.recallTime = "2023-10-15T15:30:00+00:00"
-- Ожидаемый результат: 1697382600 (Unix timestamp)
-- Категория: LowCode - конвертация времени
-- Теги: unix_timestamp, date, time, wf.initVariables, ISO8601, parsing

local iso_time = wf.initVariables.recallTime
local days_in_month = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}

if not iso_time or not iso_time:match("^%d%d%d%d%-%d%d%-%d%dT") then
    return nil
end

local function is_leap_year(year)
    return (year % 4 == 0 and year % 100 ~= 0) or (year % 400 == 0)
end

local function days_since_epoch(year, month, day)
    local days = 0
    for y = 1970, year - 1 do
        days = days + (is_leap_year(y) and 366 or 365)
    end
    for m = 1, month - 1 do
        days = days + days_in_month[m]
        if m == 2 and is_leap_year(year) then
            days = days + 1
        end
    end
    days = days + (day - 1)
    return days
end

local function parse_iso8601_to_epoch(iso_str)
    if not iso_str then
        error("Дата не задана (nil)")
    end

    -- Пробуем с миллисекундами
    local year, month, day, hour, min, sec, ms, offset_sign, offset_hour, offset_min =
        iso_str:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)%.(%d+)([+-])(%d+):(%d+)")

    -- Если не удалось — пробуем без миллисекунд
    if not year then
        year, month, day, hour, min, sec, offset_sign, offset_hour, offset_min =
            iso_str:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)([+-])(%d+):(%d+)")
        ms = 0
    end

    if not year then
        error("Невозможно разобрать дату: " .. tostring(iso_str))
    end

    year = tonumber(year)
    month = tonumber(month)
    day = tonumber(day)
    hour = tonumber(hour)
    min = tonumber(min)
    sec = tonumber(sec)
    ms = tonumber(ms) or 0
    offset_hour = tonumber(offset_hour)
    offset_min = tonumber(offset_min)

    local total_days = days_since_epoch(year, month, day)
    local total_seconds = total_days * 86400 + hour * 3600 + min * 60 + sec

    local offset_seconds = offset_hour * 3600 + offset_min * 60
    if offset_sign == "-" then
        offset_seconds = -offset_seconds
    end

    return total_seconds - offset_seconds
end

local epoch_seconds = parse_iso8601_to_epoch(iso_time)
return epoch_seconds
