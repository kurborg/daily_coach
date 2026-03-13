import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
_cache = None


def get_config() -> dict:
    global _cache
    if _cache is None:
        with open(_CONFIG_PATH, "r") as f:
            _cache = json.load(f)
    return _cache


def get_targets() -> dict:
    return get_config()["daily_targets"]


def get_events() -> list:
    return get_config()["events"]


def get_goals() -> dict:
    return get_config()["goals"]
