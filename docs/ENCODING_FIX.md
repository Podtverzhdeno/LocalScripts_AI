# Исправление проблемы кодировки UTF-8 на Windows

## Проблема

```
'charmap' codec can't decode byte 0x98 in position 3626: character maps to <undefined>
```

**Причина:** На Windows Python по умолчанию использует кодировку `cp1252` (charmap) при открытии файлов. Файлы с UTF-8 символами (эмодзи ✅, ❌, ⚠️, 🚀) вызывают ошибку декодирования.

## Исправленные файлы

### 1. `config/loader.py` (критично!)

**Строка 18:**
```python
# Было:
with open(path) as f:
    return yaml.safe_load(f)

# Стало:
with open(path, encoding="utf-8") as f:
    return yaml.safe_load(f)
```

**Строка 38:**
```python
# Было:
with open(path) as f:
    return yaml.safe_load(f)

# Стало:
with open(path, encoding="utf-8") as f:
    return yaml.safe_load(f)
```

### 2. `test_simple.py`

**Строка 128:**
```python
# Было:
final_code = (session_dir / "final.lua").read_text()

# Стало:
final_code = (session_dir / "final.lua").read_text(encoding="utf-8")
```

## Почему это важно

1. **Файлы с эмодзи:** Документация (`*.md`) содержит UTF-8 символы
2. **YAML конфиги:** `agents.yaml` может содержать комментарии с эмодзи
3. **Кросс-платформенность:** Linux/Mac используют UTF-8 по умолчанию, Windows - нет

## Проверка

Все остальные файлы уже используют `encoding="utf-8"`:
- ✅ `graph/nodes.py` - все операции с файлами
- ✅ `api/routes.py` - все операции с файлами
- ✅ `tools/lua_runner.py` - все операции с файлами
- ✅ `main.py` - все операции с файлами

## Тестирование

```bash
# Должно работать без ошибок:
python main.py --task "write fibonacci"
python api/server.py
```

## Best Practice

**Всегда указывайте encoding при работе с текстовыми файлами:**

```python
# ✅ Правильно
with open(path, encoding="utf-8") as f:
    content = f.read()

# ✅ Правильно
path.read_text(encoding="utf-8")
path.write_text(content, encoding="utf-8")

# ❌ Неправильно (зависит от системы)
with open(path) as f:
    content = f.read()

# ❌ Неправильно (зависит от системы)
path.read_text()
```

## Дата исправления

2026-04-11
