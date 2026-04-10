"""
Shared config loader — used by all modules.
Caches settings after first load to avoid repeated file reads.
Cache is automatically invalidated when config files are modified.
"""

from pathlib import Path
from functools import lru_cache
import yaml
import os

_CONFIG_DIR = Path(__file__).parent


def _get_file_mtime(filepath: Path) -> float:
    """Get file modification time, return 0 if file doesn't exist."""
    try:
        return filepath.stat().st_mtime
    except (OSError, FileNotFoundError):
        return 0.0


@lru_cache(maxsize=1)
def load_settings() -> dict:
    """Load and cache settings.yaml."""
    path = _CONFIG_DIR / "settings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# Cache with file modification time as part of the key
@lru_cache(maxsize=10)
def _load_agent_config_cached(filename: str, mtime: float) -> dict:
    """
    Internal cached loader with mtime in key.
    When file is modified, mtime changes -> cache miss -> reload.
    """
    path = _CONFIG_DIR / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_agent_config(use_small_prompts: bool = False, use_lowcode_prompts: bool = False) -> dict:
    """
    Load and cache agents.yaml, agents_small.yaml, or agents_lowcode.yaml.

    Cache is automatically invalidated when the file is modified.

    Args:
        use_small_prompts: If True, load agents_small.yaml (optimized for 7B models)
        use_lowcode_prompts: If True, load agents_lowcode.yaml (optimized for LowCode + 7B)
    """
    if use_lowcode_prompts:
        filename = "agents_lowcode.yaml"
    elif use_small_prompts:
        filename = "agents_small.yaml"
    else:
        filename = "agents.yaml"

    path = _CONFIG_DIR / filename
    mtime = _get_file_mtime(path)

    # Cache key includes mtime - when file changes, cache misses
    return _load_agent_config_cached(filename, mtime)


def get_agent_prompt(role: str) -> str:
    """
    Return the system_prompt for a given agent role.

    Priority:
    1. USE_LOWCODE_PROMPTS=true → agents_lowcode.yaml (LowCode + 7B optimized)
    2. USE_SMALL_PROMPTS=true → agents_small.yaml (7B optimized)
    3. Auto-detect small models (7b, 8b in name) → agents_small.yaml
    4. Default → agents.yaml
    """
    import os

    # Check for LowCode mode (highest priority)
    use_lowcode = os.getenv("USE_LOWCODE_PROMPTS", "").lower() == "true"

    # Check explicit small prompts env var
    use_small = os.getenv("USE_SMALL_PROMPTS", "").lower() == "true"

    # Auto-detect small models by name
    if not use_small and not use_lowcode:
        model_name = os.getenv("LLM_MODEL", "").lower()
        small_indicators = ["7b", "8b", "1b", "3b"]
        use_small = any(indicator in model_name for indicator in small_indicators)

    cfg = load_agent_config(use_small_prompts=use_small, use_lowcode_prompts=use_lowcode)
    agent = cfg.get(role, {})
    return agent.get("system_prompt", f"You are a {role} agent.")


def get_strategy_name(role: str) -> str:
    """
    Return the reasoning strategy name for a given agent role.

    Priority: GENERATOR_STRATEGY env var > settings.yaml > "none".
    """
    import os
    settings = load_settings()
    strategy_cfg = settings.get("strategy", {})
    default = strategy_cfg.get(role, "none")
    env_key = f"{role.upper()}_STRATEGY"
    return os.getenv(env_key, default)
