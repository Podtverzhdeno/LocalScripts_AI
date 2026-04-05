"""
Shared config loader — used by all modules.
Caches settings after first load to avoid repeated file reads.
"""

from pathlib import Path
from functools import lru_cache
import yaml

_CONFIG_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_settings() -> dict:
    """Load and cache settings.yaml."""
    path = _CONFIG_DIR / "settings.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_agent_config() -> dict:
    """Load and cache agents.yaml."""
    path = _CONFIG_DIR / "agents.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def get_agent_prompt(role: str) -> str:
    """Return the system_prompt for a given agent role."""
    cfg = load_agent_config()
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
