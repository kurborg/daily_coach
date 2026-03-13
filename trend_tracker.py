import json
import os
from datetime import datetime, date, timedelta
from typing import Optional


def _history_path(user_id: str) -> str:
    return os.path.join(os.path.dirname(__file__), "data", user_id, "history.json")


def _load_history(user_id: str) -> dict:
    path = _history_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save_history(user_id: str, history: dict):
    path = _history_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2, default=str)


def save_daily_summary(date_str: str, health_data_dict: dict, user_id: str):
    history = _load_history(user_id)
    history[date_str] = health_data_dict
    _save_history(user_id, history)


def _get_recent_entries(user_id: str, days: int) -> list:
    history = _load_history(user_id)
    today = date.today()
    entries = []
    for i in range(days):
        d = today - timedelta(days=i + 1)
        key = d.isoformat()
        if key in history:
            entries.append(history[key])
    return entries


def get_rolling_averages(user_id: str, days: int = 7) -> dict:
    entries = _get_recent_entries(user_id, days)
    if not entries:
        return {}
    metrics = ["steps", "active_calories", "resting_hr", "sleep_hours",
               "protein_g", "calories_consumed", "weight_lbs"]
    averages = {}
    for m in metrics:
        vals = [e[m] for e in entries if e.get(m) is not None]
        averages[m] = round(sum(vals) / len(vals), 1) if vals else None
    return averages


def get_weight_trend(user_id: str, cfg: dict) -> dict:
    history = _load_history(user_id)
    today = date.today()

    def weight_on(d: date) -> Optional[float]:
        for i in range(7):
            key = (d - timedelta(days=i)).isoformat()
            if key in history and history[key].get("weight_lbs"):
                return history[key]["weight_lbs"]
        return None

    current = weight_on(today - timedelta(days=1))
    week_ago = weight_on(today - timedelta(days=8))
    month_ago = weight_on(today - timedelta(days=31))

    lbs_lost_week = round(week_ago - current, 1) if current and week_ago else None
    lbs_lost_month = round(month_ago - current, 1) if current and month_ago else None

    projected_by_target = None
    target_date = None
    target_date_str = cfg.get("goals", {}).get("weight_cutoff_date")
    if target_date_str:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        if current and lbs_lost_week and lbs_lost_week > 0:
            days_remaining = (target_date - today).days
            projected_by_target = round(current - (lbs_lost_week * (days_remaining / 7)), 1)

    return {
        "current": current,
        "week_ago": week_ago,
        "month_ago": month_ago,
        "lbs_lost_week": lbs_lost_week,
        "lbs_lost_month": lbs_lost_month,
        "projected_by_target": projected_by_target,
        "target_date": target_date.isoformat() if target_date else None,
    }


def get_streak(metric: str, target: float, user_id: str, higher_is_better: bool = True) -> int:
    history = _load_history(user_id)
    today = date.today()
    streak = 0
    for i in range(1, 365):
        key = (today - timedelta(days=i)).isoformat()
        if key not in history:
            break
        val = history[key].get(metric)
        if val is None:
            break
        if higher_is_better and val >= target:
            streak += 1
        elif not higher_is_better and val <= target:
            streak += 1
        else:
            break
    return streak
