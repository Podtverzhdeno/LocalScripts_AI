# UI Mode Selection — Quick vs Project Mode

## Обзор изменений

Добавлена визуальная поддержка выбора режимов работы в Web UI:
- **Quick Mode** (⚡) — быстрая генерация одного файла
- **Project Mode** (🏗️) — многофайловый проект с архитектурой и эволюцией

## Что изменилось

### 1. Frontend (`frontend/index.html`)

#### Переключатель режимов
```html
<button id="quickModeBtn" onclick="switchMode('quick')">⚡ Quick Mode</button>
<button id="projectModeBtn" onclick="switchMode('project')">🏗️ Project Mode</button>
```

#### Динамическое описание
- Текст описания меняется при переключении режимов
- Добавлены информационные подсказки под кнопками

#### Project Mode форма
- **Project Requirements** — textarea для описания требований
- **Max Iterations** — максимум попыток на файл (1-10)
- **Evolution Cycles** — количество циклов улучшения (0-10)
- Тултипы с объяснениями параметров

#### Улучшенная статистика
Было (3 колонки):
- Total Sessions
- Completed
- Pending

Стало (4 колонки):
- Total Sessions
- Completed
- ⚡ Quick (количество quick-сессий)
- 🏗️ Project (количество project-сессий)

#### Визуальные бейджи в списке сессий
Каждая сессия теперь показывает:
- 🏗️ Project или ⚡ Quick бейдж
- Цветовая кодировка (violet для project, cyan для quick)

### 2. Backend (`api/routes.py`)

#### Обновлен `/api/sessions`
```python
# Теперь включает и session_*, и project_* директории
if not (entry.name.startswith("session_") or entry.name.startswith("project_")):
    continue

# Поддержка requirements.md для project mode
if task_file.exists():
    task = task_file.read_text(encoding="utf-8").strip()
elif requirements_file.exists():
    task = requirements_file.read_text(encoding="utf-8").strip()

# Определение завершенности для project mode
has_final = (entry / "final.lua").exists() or (entry / "README.md").exists()
```

### 3. JavaScript (`frontend/app.js`)

#### Функция `switchMode(mode)`
- Переключает активные кнопки
- Показывает/скрывает соответствующие формы
- Обновляет текст описания
- Переключает информационные подсказки

#### Функция `runProject()`
- Отправляет POST на `/api/run-task` с параметрами:
  - `task` — требования проекта
  - `mode: "project"`
  - `max_iterations`
  - `evolutions`
- Показывает прогресс и результат
- Обновляет список сессий после запуска

#### Обновлен `loadSessions()`
- Подсчитывает quick и project сессии отдельно
- Определяет режим по префиксу `session_id`
- Добавляет визуальные бейджи в карточки сессий

## Как использовать

### Quick Mode (по умолчанию)
1. Открыть http://127.0.0.1:8000
2. Ввести задачу в поле (например: "write fibonacci function")
3. Нажать "Run Task"
4. Получить один файл `final.lua`

### Project Mode
1. Открыть http://127.0.0.1:8000
2. Нажать "🏗️ Project Mode"
3. Ввести требования проекта в textarea:
   ```
   Create an authentication system with:
   - User registration
   - Login/logout
   - Session management
   - Password hashing
   ```
4. Настроить параметры:
   - Max Iterations: 3 (попытки на файл)
   - Evolution Cycles: 3 (циклы улучшения, 0 = без эволюции)
5. Нажать "Create Project"
6. Получить многофайловый проект в `workspace/project_TIMESTAMP/`

## Структура Project Mode

```
workspace/project_20260406_230717/
├── task.txt                    # Исходные требования
├── project_plan.json           # План архитектора
├── src/                        # Сгенерированные файлы
│   ├── config.lua
│   ├── db.lua
│   ├── auth.lua
│   └── api.lua
├── manifest.json               # Метаданные проекта
├── README.md                   # Автогенерированная документация
└── evolution_history.json      # История улучшений (если evolutions > 0)
```

## API изменения

### POST `/api/run-task`
Теперь принимает дополнительные параметры:

```json
{
  "task": "string",
  "mode": "quick" | "project",      // NEW
  "max_iterations": 3,
  "evolutions": 3                   // NEW (только для project mode)
}
```

### GET `/api/sessions`
Возвращает все сессии (и `session_*`, и `project_*`):

```json
[
  {
    "session_id": "session_20260406_234238",
    "task": "создай фибоначи",
    "has_final": true
  },
  {
    "session_id": "project_20260406_231259",
    "task": "create a simple calculator",
    "has_final": true
  }
]
```

## Визуальные улучшения

### Цветовая схема
- **Quick Mode**: cyan (#06b6d4)
- **Project Mode**: violet (#8b5cf6)
- **Completed**: emerald (#10b981)
- **In Progress**: yellow (#eab308)

### Анимации
- Плавное переключение режимов
- Fade-in для карточек сессий
- Hover-эффекты на кнопках
- Shimmer-эффект при загрузке

### Тултипы
- Появляются при наведении на иконки "?"
- Объясняют параметры Max Iterations и Evolution Cycles
- Стилизованы в темной теме

## Тестирование

```bash
# Запустить сервер
cd LocalScripts_AI
python api/server.py

# Открыть в браузере
http://127.0.0.1:8000

# Протестировать Quick Mode
1. Ввести: "write hello world"
2. Нажать "Run Task"
3. Проверить workspace/session_*/final.lua

# Протестировать Project Mode
1. Переключить на "🏗️ Project Mode"
2. Ввести: "create calculator with add/subtract"
3. Установить evolutions: 0 (для быстрого теста)
4. Нажать "Create Project"
5. Проверить workspace/project_*/src/
```

## Совместимость

- ✅ Обратная совместимость с существующими `session_*` директориями
- ✅ Работает с текущим API без breaking changes
- ✅ CLI остается без изменений (`python main.py --mode project`)
- ✅ Все существующие сессии отображаются корректно

## Будущие улучшения

- [ ] Фильтрация сессий по режиму (Quick/Project)
- [ ] Визуализация графа эволюции для Project Mode
- [ ] Предпросмотр структуры проекта перед генерацией
- [ ] Экспорт проекта в ZIP
- [ ] Сравнение версий между evolution cycles
