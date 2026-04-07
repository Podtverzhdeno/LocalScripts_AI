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


@lru_cache(maxsize=2)
def load_agent_config(use_small_prompts: bool = False) -> dict:
    """
    Load and cache agents.yaml or agents_small.yaml.

    Args:
        use_small_prompts: If True, load agents_small.yaml (optimized for 7B models)
    """
    filename = "agents_small.yaml" if use_small_prompts else "agents.yaml"
    path = _CONFIG_DIR / filename
    with open(path) as f:
        return yaml.safe_load(f)


def get_agent_prompt(role: str) -> str:
    """
    Return the system_prompt for a given agent role.

    Automatically uses agents_small.yaml if USE_SMALL_PROMPTS=true in env
    or if model name suggests a small model (7b, 8b in name).
    """
    import os

    # Check explicit env var
    use_small = os.getenv("USE_SMALL_PROMPTS", "").lower() == "true"

    # Auto-detect small models by name
    if not use_small:
        model_name = os.getenv("LLM_MODEL", "").lower()
        small_indicators = ["7b", "8b", "1b", "3b"]
        use_small = any(indicator in model_name for indicator in small_indicators)

    cfg = load_agent_config(use_small_prompts=use_small)
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
