# Очистка кэша конфигурации

## Проблема

После обновления промптов в `config/agents.yaml`, старые промпты могут оставаться в кэше из-за `@lru_cache` в `config/loader.py`.

**Симптомы:**
- Test Generator генерирует старые тесты после обновления промпта
- Изменения в `agents.yaml` не применяются
- Нужно перезапускать Python для применения изменений

## Решение 1: Очистка кэша через Python

```bash
cd LocalScripts_AI
python -c "from config.loader import load_agent_config; load_agent_config.cache_clear(); print('Cache cleared')"
```

## Решение 2: Перезапуск процесса

Просто перезапустите `main.py` или `api/server.py` - кэш очистится автоматически.

## Решение 3: Отключить кэш (для разработки)

Временно закомментируйте `@lru_cache` в `config/loader.py`:

```python
# @lru_cache(maxsize=3)  # Закомментировать для разработки
def load_agent_config(use_small_prompts: bool = False, use_lowcode_prompts: bool = False) -> dict:
    ...
```

**Важно:** Не забудьте вернуть кэш для production!

## Автоматическая очистка

Кэш очищается автоматически при:
- Перезапуске Python процесса
- Изменении параметров `use_small_prompts` или `use_lowcode_prompts`

## Проверка текущего промпта

```python
from config.loader import get_agent_prompt
prompt = get_agent_prompt('test_generator')
print(prompt[:200])  # Первые 200 символов
```

## Дата

2026-04-11
