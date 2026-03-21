import json
import os

USERS_DIR = os.path.join(os.path.dirname(__file__), "users")


def load_all_users() -> list[dict]:
    """
    Load all user configs.

    If DAILY_COACH_CONFIGS_FOLDER is set, configs are loaded from that Google
    Drive folder (shared with the service account). Local users/*.json files are
    also loaded as a fallback/supplement — useful for local dev and for users
    whose configs haven't been migrated to Drive yet. Drive configs take
    precedence: a local file with the same user_id as a Drive config is skipped.
    """
    configs = []

    # 1. Drive configs (primary for production)
    configs_folder = os.environ.get("DAILY_COACH_CONFIGS_FOLDER")
    if configs_folder:
        from drive_client import load_user_configs_from_drive
        configs.extend(load_user_configs_from_drive(configs_folder))

    # 2. Local users/ (fallback / dev)
    drive_ids = {c["_user_id"] for c in configs}
    if os.path.isdir(USERS_DIR):
        for fname in sorted(os.listdir(USERS_DIR)):
            if fname.endswith(".json") and not fname.startswith("_"):
                user_id = fname[:-5]
                if user_id in drive_ids:
                    continue  # Drive version takes precedence
                with open(os.path.join(USERS_DIR, fname)) as f:
                    cfg = json.load(f)
                    cfg["_user_id"] = user_id
                    configs.append(cfg)

    return sorted(configs, key=lambda c: c["_user_id"])


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
