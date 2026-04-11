-- Задача: Для полученных данных из предыдущего REST запроса очисти значения переменных ID, ENTITY_ID, CALL
-- Контекст: wf.vars.RESTbody.result = массив объектов с различными ключами
-- Ожидаемый результат: массив объектов только с ключами ID, ENTITY_ID, CALL
-- Категория: LowCode - фильтрация объектов
-- Теги: filter, object, keys, wf.vars, REST, pairs

result = wf.vars.RESTbody.result

for _, filteredEntry in pairs(result) do
    for key, value in pairs(filteredEntry) do
        if key ~= "ID" and key ~= "ENTITY_ID" and key ~= "CALL" then
            filteredEntry[key] = nil
        end
    end
end

return result
