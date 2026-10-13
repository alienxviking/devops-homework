import os

import yaml

DEFAULTS = {"max_tasks": 100, "app_name": "Secure Tasks API"}


def load_config(path=None):
    """Read optional YAML settings. safe_load never builds arbitrary python objects."""
    path = path or os.getenv("APP_CONFIG", "config.yaml")
    settings = dict(DEFAULTS)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            settings.update(yaml.safe_load(f) or {})
    return settings
