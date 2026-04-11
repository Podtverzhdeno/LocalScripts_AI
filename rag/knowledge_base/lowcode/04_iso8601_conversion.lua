-- Задача: Преобразуй время из формата 'YYYYMMDD' и 'HHMMSS' в строку в формате ISO 8601
-- Контекст: wf.vars.json.IDOC.ZCDF_HEAD.DATUM = "20231015", TIME = "153000"
-- Ожидаемый результат: "2023-10-15T15:30:00.00000Z"
-- Категория: LowCode - работа с датами
-- Теги: date, time, ISO8601, format, string, wf.vars

DATUM = wf.vars.json.IDOC.ZCDF_HEAD.DATUM
TIME = wf.vars.json.IDOC.ZCDF_HEAD.TIME

local function safe_sub(str, start, finish)
    local s = string.sub(str, start, math.min(finish, #str))
    return s ~= "" and s or "00"
end

year = safe_sub(DATUM, 1, 4)
month = safe_sub(DATUM, 5, 6)
day = safe_sub(DATUM, 7, 8)
hour = safe_sub(TIME, 1, 2)
minute = safe_sub(TIME, 3, 4)
second = safe_sub(TIME, 5, 6)

iso_date = string.format(
    '%s-%s-%sT%s:%s:%s.00000Z',
    year, month, day,
    hour, minute, second
)

return iso_date
