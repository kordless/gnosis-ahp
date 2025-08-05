import os
import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".geminicli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

def ensure_config_dir_exists():
    """Ensures the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    """Loads the configuration from the YAML file."""
    ensure_config_dir_exists()
    if not CONFIG_FILE.is_file():
        return {}
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f) or {}

def save_config(config: dict):
    """Saves the configuration to the YAML file."""
    ensure_config_dir_exists()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

def get_config_value(key: str, default=None):
    """Gets a specific value from the config."""
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value):
    """Sets a specific value in the config."""
    config = load_config()
    config[key] = value
    save_config(config)
