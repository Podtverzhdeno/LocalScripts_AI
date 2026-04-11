-- Задача: Из полученного списка email получи последний
-- Контекст: wf.vars.emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
-- Ожидаемый результат: "user3@example.com"
-- Категория: LowCode - работа с массивами
-- Теги: array, wf.vars, last_element, indexing

return wf.vars.emails[#wf.vars.emails]
