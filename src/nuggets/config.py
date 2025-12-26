"""Configuration management for Podcast Nuggets.

Save and load analysis configurations for reuse across similar podcasts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nuggets.models import AnalysisConfig

# Default config directory
CONFIG_DIR = Path("data/configs")


def get_config_dir() -> Path:
    """Get the config directory, creating it if necessary."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def list_configs() -> list[dict]:
    """List all saved configurations.

    Returns:
        List of dicts with name, description, and path for each config.
    """
    config_dir = get_config_dir()
    configs = []

    for config_file in sorted(config_dir.glob("*.json")):
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
            configs.append({
                "name": data.get("name", config_file.stem),
                "description": data.get("description", ""),
                "path": str(config_file),
                "theme_count": len(data.get("theme_configs", [])),
            })
        except (json.JSONDecodeError, OSError):
            continue

    return configs


def load_config(name: str) -> "AnalysisConfig":
    """Load a saved configuration by name.

    Args:
        name: Config name (without .json extension).

    Returns:
        AnalysisConfig instance.

    Raises:
        FileNotFoundError: If config doesn't exist.
        ValueError: If config is invalid.
    """
    from nuggets.models import AnalysisConfig

    config_dir = get_config_dir()
    config_file = config_dir / f"{name}.json"

    if not config_file.exists():
        raise FileNotFoundError(f"Config not found: {name}")

    with open(config_file, encoding="utf-8") as f:
        data = json.load(f)

    return AnalysisConfig.model_validate(data)


def save_config(config: "AnalysisConfig", name: str | None = None) -> Path:
    """Save a configuration for later reuse.

    Args:
        config: The AnalysisConfig to save.
        name: Optional name override (uses config.name if not provided).

    Returns:
        Path to the saved config file.

    Raises:
        ValueError: If no name is provided and config.name is None.
    """
    config_name = name or config.name
    if not config_name:
        raise ValueError("Config must have a name to be saved")

    # Update config name if overridden
    if name and config.name != name:
        config = config.model_copy(update={"name": name})

    config_dir = get_config_dir()
    config_file = config_dir / f"{config_name}.json"

    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2))

    return config_file


def delete_config(name: str) -> bool:
    """Delete a saved configuration.

    Args:
        name: Config name to delete.

    Returns:
        True if deleted, False if not found.
    """
    config_dir = get_config_dir()
    config_file = config_dir / f"{name}.json"

    if config_file.exists():
        config_file.unlink()
        return True
    return False


def config_exists(name: str) -> bool:
    """Check if a config with the given name exists."""
    config_dir = get_config_dir()
    return (config_dir / f"{name}.json").exists()
