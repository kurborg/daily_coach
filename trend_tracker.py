import json
import os
from datetime import datetime, date, timedelta
from typing import Optional

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "data", "history.json")
WEIGHT_TARGET_DATE = date(2026, 6, 15)


def _load_history() -> dict:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    if not os.path.exists(HISTORY_PATH):
        return {}
    with open(HISTORY_PATH, "r") as f:
        return json.load(f)


def _save_history(history: dict):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2, default=str)


def save_daily_summary(date_str: str, health_data_dict: dict):
    history = _load_history()
    history[date_str] = health_data_dict
    _save_history(history)


def _get_recent_entries(days: int) -> list:
    history = _load_history()
    today = date.today()
    entries = []
    for i in range(days):
        d = today - timedelta(days=i + 1)
        key = d.isoformat()
        if key in history:
            entries.append(history[key])
    return entries


def get_rolling_averages(days: int = 7) -> dict:
    entries = _get_recent_entries(days)
    if not entries:
        return {}

    metrics = ["steps", "active_calories", "resting_hr", "sleep_hours",
               "protein_g", "calories_consumed", "weight_lbs"]
    averages = {}
    for m in metrics:
        vals = [e[m] for e in entries if e.get(m) is not None]
        averages[m] = round(sum(vals) / len(vals), 1) if vals else None
    return averages


def get_weight_trend() -> dict:
    history = _load_history()
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

    lbs_lost_week = None
    lbs_lost_month = None
    projected_by_target = None

    if current is not None and week_ago is not None:
        lbs_lost_week = round(week_ago - current, 1)

    if current is not None and month_ago is not None:
        lbs_lost_month = round(month_ago - current, 1)

    if current is not None and lbs_lost_week is not None and lbs_lost_week > 0:
        days_remaining = (WEIGHT_TARGET_DATE - today).days
        weekly_rate = lbs_lost_week
        weeks_remaining = days_remaining / 7
        projected_by_target = round(current - (weekly_rate * weeks_remaining), 1)

    return {
        "current": current,
        "week_ago": week_ago,
        "month_ago": month_ago,
        "lbs_lost_week": lbs_lost_week,
        "lbs_lost_month": lbs_lost_month,
        "projected_by_target": projected_by_target,
        "target_date": WEIGHT_TARGET_DATE.isoformat(),
    }


def get_streak(metric: str, target: float, higher_is_better: bool = True) -> int:
    history = _load_history()
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
