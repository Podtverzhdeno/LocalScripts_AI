-- Задача: Преобразовать структуру данных так, чтобы все элементы items в ZCDF_PACKAGES всегда были представлены в виде массивов
-- Контекст: wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES - массив объектов, где items может быть объектом или массивом
-- Ожидаемый результат: все items гарантированно массивы
-- Категория: LowCode - проверка типов
-- Теги: type_check, array, ensure, wf.vars, ipairs

function ensureArray(t)
    if type(t) ~= "table" then
        return {t}
    end
    local isArray = true
    for k, v in pairs(t) do
        if type(k) ~= "number" or math.floor(k) ~= k then
            isArray = false
            break
        end
    end
    return isArray and t or {t}
end

function ensureAllItemsAreArrays(objectsArray)
    if type(objectsArray) ~= "table" then
        return objectsArray
    end
    for _, obj in ipairs(objectsArray) do
        if type(obj) == "table" and obj.items then
            obj.items = ensureArray(obj.items)
        end
    end
    return objectsArray
end

return ensureAllItemsAreArrays(wf.vars.json.IDOC.ZCDF_HEAD.ZCDF_PACKAGES)
