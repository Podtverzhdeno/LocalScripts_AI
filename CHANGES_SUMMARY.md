# 🎨 UI Improvements: Mode Selection (Quick vs Project)

## ✨ Что добавлено

### 1. Визуальный переключатель режимов
```
┌─────────────────────────────────────────┐
│  [⚡ Quick Mode]  [🏗️ Project Mode]    │
│   (активная)        (неактивная)        │
└─────────────────────────────────────────┘
```

**Quick Mode** — быстрая генерация одного файла  
**Project Mode** — многофайловый проект с эволюцией

### 2. Динамические формы ввода

#### Quick Mode (по умолчанию)
```
┌──────────────────────────────────────────────────┐
│ [write a fibonacci function...]  [▶ Run Task]   │
└──────────────────────────────────────────────────┘
```

#### Project Mode
```
┌──────────────────────────────────────────────────┐
│ Project Requirements:                            │
│ ┌──────────────────────────────────────────────┐ │
│ │ Create an authentication system with:        │ │
│ │ - User registration                          │ │
│ │ - Login/logout                               │ │
│ │ - Session management                         │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ ┌──────────────┐  ┌──────────────────────────┐  │
│ │ Max Iterations│  │ Evolution Cycles (?)     │  │
│ │      [3]     │  │      [3]                 │  │
│ └──────────────┘  └──────────────────────────┘  │
│                                                  │
│         [🏗️ Create Project]                     │
└──────────────────────────────────────────────────┘
```

### 3. Улучшенная статистика

**Было:**
```
┌─────────┬───────────┬─────────┐
│  Total  │ Completed │ Pending │
│   42    │    38     │    4    │
└─────────┴───────────┴─────────┘
```

**Стало:**
```
┌─────────┬───────────┬─────────┬──────────┐
│  Total  │ Completed │ ⚡ Quick │ 🏗️ Project│
│   42    │    38     │   35    │    7     │
└─────────┴───────────┴─────────┴──────────┘
```

### 4. Визуальные бейджи в списке сессий

**Было:**
```
┌────────────────────────────────────────────┐
│ ● создай фибоначи                          │
│   20260406 @ 234238  |  Completed          │
└────────────────────────────────────────────┘
```

**Стало:**
```
┌────────────────────────────────────────────┐
│ ● [⚡ Quick]                                │
│   создай фибоначи                          │
│   20260406 @ 234238  |  Completed          │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ ● [🏗️ Project]                             │
│   create authentication system             │
│   20260406 @ 230717  |  In Progress        │
└────────────────────────────────────────────┘
```

### 5. Тултипы с подсказками

При наведении на иконку "?" рядом с параметрами:

```
Max Iterations (?)
     ↓
┌─────────────────────────────────────┐
│ Max retry attempts per file if     │
│ validation fails                    │
└─────────────────────────────────────┘

Evolution Cycles (?)
     ↓
┌─────────────────────────────────────┐
│ Number of improvement iterations    │
│ after initial generation.           │
│ 0 = no evolution, just create files │
└─────────────────────────────────────┘
```

## 📝 Измененные файлы

### Frontend
- ✅ `frontend/index.html` — добавлен переключатель режимов, формы, статистика
- ✅ `frontend/app.js` — функции `switchMode()` и `runProject()`

### Backend
- ✅ `api/routes.py` — поддержка `project_*` сессий в `/api/sessions`
- ✅ `api/models.py` — добавлены поля `mode` и `evolutions` в `RunTaskRequest`

### Документация
- ✅ `docs/UI_MODE_SELECTION.md` — полная документация изменений

## 🎯 Как работает

### Quick Mode (⚡)
1. Пользователь вводит задачу: "write fibonacci"
2. Нажимает "Run Task"
3. Система создает `workspace/session_TIMESTAMP/`
4. Генерирует один файл `final.lua`
5. Показывает результат

### Project Mode (🏗️)
1. Пользователь переключается на Project Mode
2. Вводит требования проекта (многострочный текст)
3. Настраивает параметры:
   - **Max Iterations**: 3 (попытки на файл)
   - **Evolution Cycles**: 3 (циклы улучшения)
4. Нажимает "Create Project"
5. Система:
   - Создает `workspace/project_TIMESTAMP/`
   - **Architect** планирует структуру
   - **Generator** создает файлы
   - **Validator** проверяет каждый файл
   - **Reviewer** одобряет код
   - **Decomposer** анализирует проект
   - **Evolver** улучшает код (если evolutions > 0)
6. Результат: многофайловый проект с README.md

## 🎨 Цветовая схема

| Элемент | Цвет | Hex |
|---------|------|-----|
| Quick Mode | Cyan | `#06b6d4` |
| Project Mode | Violet | `#8b5cf6` |
| Completed | Emerald | `#10b981` |
| In Progress | Yellow | `#eab308` |
| Failed | Red | `#ef4444` |

## 🚀 Запуск

```bash
cd LocalScripts_AI
python api/server.py
# Открыть http://127.0.0.1:8000
```

## ✅ Тестирование

### Quick Mode
```bash
# В браузере:
1. Ввести: "write hello world"
2. Нажать "Run Task"
3. Проверить: workspace/session_*/final.lua
```

### Project Mode
```bash
# В браузере:
1. Нажать "🏗️ Project Mode"
2. Ввести:
   Create a calculator with:
   - Add function
   - Subtract function
   - Main entry point
3. Max Iterations: 3
4. Evolution Cycles: 0 (для быстрого теста)
5. Нажать "Create Project"
6. Проверить: workspace/project_*/src/
```

## 📊 Результаты

### Quick Mode Output
```
workspace/session_20260406_234238/
├── task.txt
├── iteration_1.lua
├── final.lua
└── report.md
```

### Project Mode Output
```
workspace/project_20260406_231259/
├── task.txt
├── project_plan.json
├── src/
│   ├── config.lua
│   ├── calculator.lua
│   └── main.lua
├── manifest.json
├── README.md
└── evolution_history.json (если evolutions > 0)
```

## 🎉 Преимущества

1. **Интуитивный выбор** — пользователь сразу видит два режима
2. **Контекстные подсказки** — описание меняется при переключении
3. **Визуальное различие** — цветовые бейджи и иконки
4. **Детальная статистика** — отдельный подсчет Quick/Project сессий
5. **Тултипы** — объяснение сложных параметров
6. **Обратная совместимость** — старые сессии работают без изменений

## 🔮 Будущие улучшения

- [ ] Фильтр сессий по режиму (показать только Quick или только Project)
- [ ] Визуализация графа эволюции для Project Mode
- [ ] Предпросмотр структуры проекта перед генерацией
- [ ] Экспорт проекта в ZIP-архив
- [ ] Diff-просмотр между evolution cycles
- [ ] Настройки стратегий рассуждения (reflect/cot) через UI
- [ ] Выбор sandbox mode (lua/docker/none) через UI

---

**Автор:** Claude Sonnet 4.5  
**Дата:** 2026-04-07  
**Версия:** LocalScript v0.1.0
