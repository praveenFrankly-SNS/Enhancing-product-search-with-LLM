# =====================================================================
# Product Search — Shared: Config Loader
# =====================================================================
# Reads config/pipeline.yml merged with config/{env}.yml.
# All pipeline scripts call load_config() to get resolved settings.
# =====================================================================

import os
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Resolves the project root by walking up directories until
    config/pipeline.yml is found.
    """
    try:
        current_dir = Path(__file__).parent.resolve()
        for path in [current_dir] + list(current_dir.parents):
            if (path / "config" / "pipeline.yml").exists():
                return path
    except NameError:
        pass
    cwd = Path(os.getcwd()).resolve()
    for path in [cwd] + list(cwd.parents):
        if (path / "config" / "pipeline.yml").exists():
            return path
    raise RuntimeError(
        "Could not determine project root. "
        "Ensure config/pipeline.yml exists in the project directory."
    )


def add_project_to_path():
    """Adds the project root to sys.path so relative imports work."""
    root_str = str(get_project_root())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def load_config(env: Optional[str] = None) -> dict:
    """
    Loads the centralized pipeline configuration from config/pipeline.yml,
    then deep-merges config/{env}.yml overrides on top of it.

    Args:
        env: Target environment name ('dev', 'staging', 'prod').
             If None, falls back to PIPELINE_ENV env var, then 'dev'.

    Returns:
        Merged configuration dictionary.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required. Add 'pyyaml' to your cluster libraries."
        )

    root = get_project_root()
    env = env or os.getenv("PIPELINE_ENV", "dev")

    # Load base config
    base_path = root / "config" / "pipeline.yml"
    if not base_path.exists():
        raise FileNotFoundError(f"Base config not found: {base_path}")
    with open(base_path) as f:
        config = yaml.safe_load(f) or {}

    # Load and merge env-specific overrides
    env_path = root / "config" / f"{env}.yml"
    if env_path.exists():
        with open(env_path) as f:
            env_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, env_config)

    config["_env"] = env
    config["_root"] = str(root)
    return config


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merges override into base, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
