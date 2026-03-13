import json
import os

USERS_DIR = os.path.join(os.path.dirname(__file__), "users")


def load_all_users() -> list[dict]:
    """Load all user configs from users/*.json, sorted by filename."""
    configs = []
    for fname in sorted(os.listdir(USERS_DIR)):
        if fname.endswith(".json") and not fname.startswith("_"):
            with open(os.path.join(USERS_DIR, fname)) as f:
                cfg = json.load(f)
                cfg["_user_id"] = fname[:-5]  # strip .json
                configs.append(cfg)
    return configs


def load_user(user_id: str) -> dict:
    path = os.path.join(USERS_DIR, f"{user_id}.json")
    with open(path) as f:
        cfg = json.load(f)
    cfg["_user_id"] = user_id
    return cfg


def resolve_ref(cfg: dict, ref: str):
    """Resolve a dotted config reference like 'goals.weight_target_lbs'."""
    section, key = ref.split(".", 1)
    return cfg[section][key]


# Keep these for backward compat with any remaining callers
def get_config() -> dict:
    raise RuntimeError("get_config() is not available in multi-user mode. Pass cfg explicitly.")


def get_targets() -> dict:
    raise RuntimeError("Use cfg['daily_targets'] directly.")


def get_events() -> list:
    raise RuntimeError("Use cfg['events'] directly.")


def get_goals() -> dict:
    raise RuntimeError("Use cfg['goals'] directly.")
