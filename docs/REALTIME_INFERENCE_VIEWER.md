# 🔥 Real-Time Inference Viewer

## Обзор

**Real-Time Inference Viewer** — интерактивное окно для просмотра генерации кода в реальном времени. Показывает:
- Текущий агент (Generator/Validator/Reviewer)
- Генерируемый код посимвольно
- Статистику: токены/сек, время, количество символов
- Прогресс итераций

## 🎯 Возможности

### 1. Live Token Streaming
- Код появляется посимвольно по мере генерации
- Плавная анимация fadeIn для каждого символа
- Автоскролл к последнему токену

### 2. Agent Tracking
- Визуальная индикация текущего агента
- Иконки: ✍️ Generator, 🔍 Validator, 👁️ Reviewer
- Описание действия агента
- Spinner во время работы

### 3. Real-Time Stats
- **Tokens/sec** — скорость генерации
- **Elapsed** — время с начала генерации
- **Characters** — общее количество символов

### 4. Controls
- **Clear** — очистить вывод
- **Close** — закрыть окно
- Автоматическое обновление при смене агента

## 🚀 Как использовать

### Открыть Inference Viewer

1. Перейти на страницу сессии: `/session/{session_id}`
2. Нажать кнопку **"Live Inference"** в header графа
3. Окно откроется поверх страницы

### Во время генерации

Окно автоматически:
- Обновляется при смене агента
- Показывает генерируемый код
- Считает статистику
- Останавливает индикаторы по завершении

### После завершения

- Код остается в окне для просмотра
- Можно очистить через кнопку "Clear"
- Закрыть через кнопку "Close" или ESC

## 🏗️ Архитектура

### Backend (API)

#### WebSocket Events

**Отправляемые события:**

```javascript
// Смена агента
{
  "event": "node_enter",
  "node": "generate",
  "agent": "generate",
  "iteration": 1,
  "status": "generating"
}

// Токен кода (симуляция streaming)
{
  "event": "token",
  "token": "local ",
  "agent": "generate"
}

// Завершение
{
  "event": "completed",
  "status": "done",
  "iteration": 1
}
```

#### Code Streaming

В `api/routes.py`:

```python
def code_callback(code: str, agent: str):
    """Симулирует streaming отправкой кода по частям."""
    chunk_size = 10  # символов на chunk
    for i in range(0, len(code), chunk_size):
        chunk = code[i:i+chunk_size]
        asyncio.run_coroutine_threadsafe(
            _broadcast(session_id, {
                "event": "token",
                "token": chunk,
                "agent": agent,
            }),
            loop
        )
        time.sleep(0.01)  # задержка для эффекта streaming
```

### Frontend (UI)

#### HTML Structure

```html
<div id="inferenceModal" class="hidden fixed inset-0 ...">
  <!-- Header -->
  <div class="px-6 py-4 border-b ...">
    <h3>Real-Time Inference</h3>
    <span id="inferenceAgent">—</span>
  </div>
  
  <!-- Current Agent Status -->
  <div class="glass rounded-xl ...">
    <div id="inferenceAgentIcon">⚡</div>
    <p id="inferenceAgentName">Waiting...</p>
    <p id="inferenceAgentDesc">Pipeline will start soon</p>
  </div>
  
  <!-- Token Stream -->
  <div id="inferenceOutput" class="font-mono ...">
    <!-- Tokens appear here -->
  </div>
  
  <!-- Stats -->
  <div class="grid grid-cols-3 ...">
    <p id="inferenceTokensPerSec">—</p>
    <p id="inferenceElapsed">—</p>
    <p id="inferenceChars">—</p>
  </div>
</div>
```

#### JavaScript Functions

**Открыть/закрыть:**
```javascript
function showInferenceViewer() {
    document.getElementById('inferenceModal').classList.remove('hidden');
}

function hideInferenceViewer() {
    document.getElementById('inferenceModal').classList.add('hidden');
}
```

**Обновить агента:**
```javascript
function updateInferenceAgent(agent, iteration) {
    inferenceState.currentAgent = agent;
    inferenceState.startTime = Date.now();
    inferenceState.tokens = [];
    
    const agentData = {
        generate: { name: 'Generator', icon: '✍️', desc: 'Writing Lua code' },
        validate: { name: 'Validator', icon: '🔍', desc: 'Compiling and executing' },
        review: { name: 'Reviewer', icon: '👁️', desc: 'Checking code quality' }
    };
    
    // Update UI...
}
```

**Добавить токен:**
```javascript
function appendInferenceToken(token) {
    inferenceState.tokens.push(token);
    inferenceState.tokenCount++;
    
    const span = document.createElement('span');
    span.textContent = token;
    span.className = 'inline-block animate-fadeIn';
    outputEl.appendChild(span);
    
    // Update stats
    const elapsed = (Date.now() - inferenceState.startTime) / 1000;
    const tokensPerSec = inferenceState.tokenCount / elapsed;
    // ...
}
```

**WebSocket обработка:**
```javascript
ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    
    if (msg.event === 'token') {
        appendInferenceToken(msg.token);
    }
    else if (msg.event === 'node_enter') {
        updateInferenceAgent(msg.agent, msg.iteration);
    }
    else if (msg.event === 'completed') {
        stopInferenceStreaming();
    }
};
```

## 🎨 Визуальный дизайн

### Цветовая схема

| Элемент | Цвет | Hex |
|---------|------|-----|
| Generator | Emerald | `#10b981` |
| Validator | Cyan | `#06b6d4` |
| Reviewer | Violet | `#8b5cf6` |
| Background | Dark | `#0a0f1a` |
| Glass | Translucent | `rgba(15,23,42,0.6)` |

### Анимации

**fadeIn** — плавное появление токенов:
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.animate-fadeIn {
    animation: fadeIn 0.2s ease-out;
}
```

**pulse** — индикатор streaming:
```css
.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

**spin** — spinner агента:
```css
.animate-spin {
    animation: spin 1s linear infinite;
}
```

## 📊 Производительность

### Chunk Size

Размер chunk влияет на:
- **Маленький (5-10 chars)**: плавнее, но больше WebSocket сообщений
- **Большой (50-100 chars)**: быстрее, но менее плавно

Текущее значение: **10 символов**

### Задержка

Задержка между chunks:
- **0.01s (10ms)**: баланс между плавностью и скоростью
- Можно настроить в `api/routes.py` → `code_callback`

### WebSocket

- Одно соединение на сессию
- Автоматический reconnect при разрыве
- Broadcast всем подключенным клиентам

## 🔧 Настройка

### Изменить chunk size

В `api/routes.py`:
```python
def code_callback(code: str, agent: str):
    chunk_size = 20  # Увеличить для быстрее
    # ...
```

### Изменить задержку

В `api/routes.py`:
```python
time.sleep(0.005)  # Уменьшить для быстрее
```

### Отключить streaming

Закомментировать в `api/routes.py`:
```python
# if code_callback:
#     code_callback(code, "generate")
```

## 🐛 Troubleshooting

### Токены не появляются

1. Проверить WebSocket соединение:
   - Открыть DevTools → Network → WS
   - Должно быть соединение к `/api/ws/{session_id}`

2. Проверить события:
   - В Live Log должны появляться `[token]` события
   - Если нет — проверить backend

3. Проверить модальное окно:
   - Убедиться что окно открыто (не `hidden`)
   - Проверить `inferenceOutput` элемент

### Медленная генерация

1. Увеличить `chunk_size` в `code_callback`
2. Уменьшить `time.sleep` задержку
3. Отключить анимации в CSS

### Статистика не обновляется

Проверить `inferenceState.startTime`:
```javascript
console.log(inferenceState);
```

Должно быть установлено при `updateInferenceAgent`.

## 📝 Примеры использования

### Пример 1: Просмотр генерации

```
1. Запустить Quick Mode task: "write fibonacci"
2. Открыть session page
3. Нажать "Live Inference"
4. Наблюдать генерацию кода в реальном времени
```

### Пример 2: Отладка медленной генерации

```
1. Открыть Inference Viewer
2. Запустить сложную задачу
3. Смотреть Tokens/sec
4. Если < 10 tok/s — проверить LLM backend
```

### Пример 3: Сравнение агентов

```
1. Открыть Inference Viewer
2. Запустить задачу с ошибками (несколько итераций)
3. Наблюдать:
   - Generator: пишет код
   - Validator: показывает ошибки
   - Reviewer: дает feedback
```

## 🚀 Будущие улучшения

- [ ] Настоящий token streaming через LangChain callbacks
- [ ] Подсветка синтаксиса в реальном времени
- [ ] Экспорт лога генерации
- [ ] Replay генерации с регулируемой скоростью
- [ ] Сравнение генераций между итерациями
- [ ] Статистика по агентам (среднее время, токены)
- [ ] Уведомления при завершении генерации

## 📚 Связанные документы

- [UI Mode Selection](UI_MODE_SELECTION.md) — выбор режимов Quick/Project
- [Architecture](architecture.md) — общая архитектура
- [Frontend Graph](frontend-graph.md) — визуализация графа

---

**Версия:** LocalScript v0.1.0  
**Дата:** 2026-04-07  
**Автор:** Claude Sonnet 4.5
