import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")

# Default settings for the queue system
DEFAULT_CONFIG = {
    "max_retries": 3,             # Maximum retry attempts before moving to DLQ
    "backoff_base": 2,            # Exponential backoff base (delay = base^attempt)
    "log_level": "INFO",          # Logging level (DEBUG, INFO, WARNING, ERROR)
    "worker_poll_interval": 1     # Seconds between worker job polling
}

def _ensure_config_dir():
    """Ensure the 'data' folder exists."""
    os.makedirs("data", exist_ok=True)

def load_config():
    """
    Load configuration from JSON file.
    If file doesn't exist, create it with default values.
    """
    _ensure_config_dir()

    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Reset config if corrupted
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(cfg):
    """Write the given config dictionary to file."""
    _ensure_config_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)

def set_config(key, value):
    """
    Update one config key and persist to file.
    Example:
        set_config("max_retries", 5)
    """
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    return cfg

def get_config_value(key):
    """
    Retrieve a single config value.
    Example:
        get_config_value("max_retries") -> 3
    """
    cfg = load_config()
    return cfg.get(key)

def reset_config():
    """Restore default configuration."""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG
