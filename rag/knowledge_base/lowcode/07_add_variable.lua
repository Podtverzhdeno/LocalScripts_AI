-- Задача: Добавь переменную с квадратом числа
-- Контекст: число '5' нужно преобразовать в число и вычислить квадрат
-- Ожидаемый результат: {"num": 5, "squared": 25}
-- Категория: LowCode - работа с переменными
-- Теги: variable, tonumber, arithmetic, multiple_variables

-- Пример использования в JSON:
-- {"num": "lua{return tonumber('5')}lua", "squared": "lua{local n = tonumber('5')\nreturn n * n}lua"}

local n = tonumber('5')
return n * n
