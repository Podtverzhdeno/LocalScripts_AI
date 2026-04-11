-- Задача: Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown
-- Контекст: wf.vars.parsedCsv - массив объектов с полями SKU, Discount, Markdown
-- Ожидаемый результат: массив объектов, где Discount или Markdown не пустые и не nil
-- Категория: LowCode - фильтрация массивов
-- Теги: filter, array, wf.vars, _utils.array, ipairs

local result = _utils.array.new()
local items = wf.vars.parsedCsv

for _, item in ipairs(items) do
    if (item.Discount ~= "" and item.Discount ~= nil) or (item.Markdown ~= "" and item.Markdown ~= nil) then
        table.insert(result, item)
    end
end

return result
