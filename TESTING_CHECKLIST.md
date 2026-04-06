# ✅ Testing Checklist — UI Mode Selection

## Статус сервера
- ✅ Сервер запущен на http://127.0.0.1:8000
- ✅ API отвечает корректно
- ✅ Frontend загружается

## 🧪 Тесты для проверки

### 1. Переключение режимов

#### Quick Mode → Project Mode
- [ ] Открыть http://127.0.0.1:8000
- [ ] По умолчанию активен Quick Mode (⚡)
- [ ] Нажать "🏗️ Project Mode"
- [ ] Проверить:
  - [ ] Кнопка Project Mode стала активной (зеленая)
  - [ ] Кнопка Quick Mode стала неактивной (серая)
  - [ ] Форма Quick Mode скрылась
  - [ ] Форма Project Mode появилась
  - [ ] Описание изменилось на "Multi-file project..."
  - [ ] Подсказка изменилась на "Multi-file • Architecture planning..."

#### Project Mode → Quick Mode
- [ ] Нажать "⚡ Quick Mode"
- [ ] Проверить:
  - [ ] Кнопка Quick Mode стала активной
  - [ ] Кнопка Project Mode стала неактивной
  - [ ] Форма Project Mode скрылась
  - [ ] Форма Quick Mode появилась
  - [ ] Описание вернулось к "Fast single-file generation..."
  - [ ] Подсказка вернулась к "Single file • Fast iteration..."

### 2. Quick Mode — Генерация кода

- [ ] Убедиться, что активен Quick Mode
- [ ] Ввести в поле: `write a function to calculate factorial`
- [ ] Нажать "Run Task"
- [ ] Проверить:
  - [ ] Кнопка показывает спиннер "Starting..."
  - [ ] Появилось сообщение "Pipeline started!"
  - [ ] Есть ссылка "View session →"
  - [ ] Список сессий обновился
  - [ ] Новая сессия появилась вверху списка
  - [ ] У сессии есть бейдж "⚡ Quick" (cyan цвет)
  - [ ] Статус "In Progress" (желтый)
- [ ] Подождать завершения (~30 сек)
- [ ] Обновить страницу
- [ ] Проверить:
  - [ ] Статус изменился на "Completed" (зеленый)
  - [ ] Статистика обновилась (Completed +1, Quick +1)

### 3. Project Mode — Создание проекта

- [ ] Переключиться на "🏗️ Project Mode"
- [ ] Ввести в textarea:
  ```
  Create a simple calculator with:
  - Add function
  - Subtract function
  - Main entry point with examples
  ```
- [ ] Установить Max Iterations: `3`
- [ ] Установить Evolution Cycles: `0` (для быстрого теста)
- [ ] Нажать "Create Project"
- [ ] Проверить:
  - [ ] Кнопка показывает спиннер "Creating Project..."
  - [ ] Появилось сообщение "Project pipeline started!"
  - [ ] Есть ссылка "View session →"
  - [ ] Список сессий обновился
  - [ ] Новая сессия с префиксом `project_`
  - [ ] У сессии есть бейдж "🏗️ Project" (violet цвет)
  - [ ] Статус "In Progress"
- [ ] Подождать завершения (~1-2 мин)
- [ ] Обновить страницу
- [ ] Проверить:
  - [ ] Статус "Completed"
  - [ ] Статистика обновилась (Completed +1, Project +1)

### 4. Статистика

- [ ] Проверить 4 колонки статистики:
  - [ ] Total Sessions (общее количество)
  - [ ] Completed (завершенные)
  - [ ] ⚡ Quick (количество quick-сессий)
  - [ ] 🏗️ Project (количество project-сессий)
- [ ] Проверить, что Total = Quick + Project
- [ ] Создать новую Quick сессию
- [ ] Проверить, что Quick +1, Total +1
- [ ] Создать новую Project сессию
- [ ] Проверить, что Project +1, Total +1

### 5. Список сессий

#### Визуальные элементы
- [ ] Каждая сессия имеет:
  - [ ] Цветную точку статуса (зеленая/желтая)
  - [ ] Бейдж режима (⚡ Quick или 🏗️ Project)
  - [ ] Текст задачи
  - [ ] Timestamp в формате "YYYYMMDD @ HHMMSS"
  - [ ] Статус (Completed / In Progress)
  - [ ] Стрелку справа

#### Цветовая кодировка
- [ ] Quick бейдж: cyan фон, cyan текст
- [ ] Project бейдж: violet фон, violet текст
- [ ] Completed статус: зеленый текст
- [ ] In Progress статус: желтый текст

#### Hover эффекты
- [ ] При наведении на карточку:
  - [ ] Карточка поднимается (translateY)
  - [ ] Появляется тень
  - [ ] Граница становится ярче

### 6. Тултипы (Project Mode)

- [ ] Переключиться на Project Mode
- [ ] Навести на "?" рядом с "Max Iterations"
- [ ] Проверить:
  - [ ] Появился тултип
  - [ ] Текст: "Max retry attempts per file if validation fails"
  - [ ] Темный фон, белая граница
- [ ] Навести на "?" рядом с "Evolution Cycles"
- [ ] Проверить:
  - [ ] Появился тултип
  - [ ] Текст: "Number of improvement iterations..."
  - [ ] Упоминание "0 = no evolution"

### 7. Валидация форм

#### Quick Mode
- [ ] Очистить поле ввода
- [ ] Нажать "Run Task"
- [ ] Проверить:
  - [ ] Появилось сообщение об ошибке
  - [ ] Текст: "Please enter a task description."
  - [ ] Красный фон, красная граница

#### Project Mode
- [ ] Переключиться на Project Mode
- [ ] Очистить textarea
- [ ] Нажать "Create Project"
- [ ] Проверить:
  - [ ] Появилось сообщение об ошибке
  - [ ] Текст: "Please enter project requirements"
  - [ ] Красный фон, красная граница

### 8. Адаптивность

#### Desktop (>1024px)
- [ ] Все элементы видны
- [ ] Статистика в 4 колонки
- [ ] Формы центрированы
- [ ] Список сессий читаем

#### Tablet (768-1024px)
- [ ] Статистика адаптируется
- [ ] Формы остаются читаемыми
- [ ] Кнопки доступны

#### Mobile (<768px)
- [ ] Переключатель режимов работает
- [ ] Формы вертикальные
- [ ] Статистика в 2 ряда
- [ ] Список сессий прокручивается

### 9. Обратная совместимость

- [ ] Старые `session_*` директории отображаются
- [ ] Старые сессии имеют бейдж "⚡ Quick"
- [ ] Статус определяется по `final.lua`
- [ ] Клик по старой сессии работает

### 10. API тесты

#### GET /api/sessions
```bash
curl http://127.0.0.1:8000/api/sessions
```
- [ ] Возвращает массив сессий
- [ ] Включает и `session_*`, и `project_*`
- [ ] Каждая сессия имеет: session_id, task, has_final

#### POST /api/run-task (Quick Mode)
```bash
curl -X POST http://127.0.0.1:8000/api/run-task \
  -H "Content-Type: application/json" \
  -d '{"task": "write hello world", "mode": "quick", "max_iterations": 3}'
```
- [ ] Возвращает session_id
- [ ] Создается `workspace/session_*/`
- [ ] Файл `task.txt` содержит задачу

#### POST /api/run-task (Project Mode)
```bash
curl -X POST http://127.0.0.1:8000/api/run-task \
  -H "Content-Type: application/json" \
  -d '{"task": "create calculator", "mode": "project", "max_iterations": 3, "evolutions": 0}'
```
- [ ] Возвращает session_id с префиксом `project_`
- [ ] Создается `workspace/project_*/`
- [ ] Файл `task.txt` содержит требования

### 11. Производительность

- [ ] Переключение режимов мгновенное (<100ms)
- [ ] Загрузка списка сессий быстрая (<500ms)
- [ ] Анимации плавные (60fps)
- [ ] Нет задержек при вводе текста

### 12. Браузерная совместимость

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (если доступен)

## 🐛 Известные проблемы

- Нет

## 📝 Примечания

- Сервер должен быть запущен: `python api/server.py`
- Для тестов с эволюцией установить `evolutions > 0` (займет больше времени)
- Workspace директория: `C:\Users\user\IdeaProjects\Check\LocalScripts_AI\workspace`

## ✅ Результаты тестирования

Дата: _____________  
Тестировщик: _____________  
Версия: LocalScript v0.1.0  

Пройдено тестов: _____ / 100+  
Критичных багов: _____  
Некритичных багов: _____  

Статус: ⬜ Passed  ⬜ Failed  ⬜ Needs Review
