from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

MILES_TO_KM = 1.60934
LBS_TO_KG = 0.453592


def _weight_as_kg(metric: Optional[dict]) -> Optional[float]:
    """Return weight in kg regardless of whether the export uses 'lb' or 'kg'."""
    if not metric or not metric.get("data"):
        return None
    entries = sorted(metric["data"], key=lambda x: x.get("date", ""), reverse=True)
    val = entries[0].get("qty")
    if val is None:
        return None
    units = metric.get("units", "").lower()
    return float(val) * LBS_TO_KG if units in ("lb", "lbs") else float(val)


@dataclass
class HealthData:
    steps: Optional[float] = None
    active_calories: Optional[float] = None
    bmr_calories: Optional[float] = None
    resting_hr: Optional[float] = None
    hrv: Optional[float] = None
    weight_kg: Optional[float] = None
    sleep_hours: Optional[float] = None
    sleep_deep_minutes: Optional[float] = None
    sleep_rem_minutes: Optional[float] = None
    sleep_core_minutes: Optional[float] = None
    sleep_bedtime: Optional[str] = None
    sleep_wake_time: Optional[str] = None
    workouts: list = field(default_factory=list)
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    calories_consumed: Optional[float] = None
    walking_running_distance_km: Optional[float] = None
    cycling_distance_km: Optional[float] = None
    swimming_distance_km: Optional[float] = None
    workout_minutes: Optional[float] = None
    body_fat_pct: Optional[float] = None

    @property
    def weight_lbs(self) -> Optional[float]:
        if self.weight_kg is not None:
            return round(self.weight_kg * 2.20462, 1)
        return None

    @property
    def tdee(self) -> Optional[float]:
        if self.active_calories is not None and self.bmr_calories is not None:
            return self.active_calories + self.bmr_calories
        return None

    @property
    def derived_activities(self) -> list:
        """
        Build activity entries from distance metrics when no workouts array exists.
        Health Auto Export daily JSON exports don't include a workouts array —
        activity is inferred from cycling_distance, walking_running_distance, and swimming_distance.
        """
        activities = []
        if self.cycling_distance_km and self.cycling_distance_km > 0.1:
            activities.append({"name": "Cycling", "distance_km": self.cycling_distance_km})
        if self.walking_running_distance_km and self.walking_running_distance_km > 0.1:
            activities.append({"name": "Walk/Run", "distance_km": self.walking_running_distance_km})
        if self.swimming_distance_km and self.swimming_distance_km > 0.01:
            activities.append({"name": "Swimming", "distance_km": self.swimming_distance_km})
        return activities

    @classmethod
    def parse(cls, raw_json: dict) -> "HealthData":
        data = raw_json.get("data", raw_json)
        metrics = {m["name"]: m for m in data.get("metrics", [])}
        workouts = data.get("workouts", [])

        def latest(metric_name: str) -> Optional[float]:
            """Return the qty from the most recent single-value entry (e.g. weight, HR)."""
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            entries = sorted(m["data"], key=lambda x: x.get("date", ""), reverse=True)
            val = entries[0].get("qty")
            return float(val) if val is not None else None

        def latest_day_sum(metric_name: str) -> Optional[float]:
            """
            Sum all entries for the most recent date.
            Required for minute-level metrics (steps, calories, distance) where
            each entry is a single minute's value, not a daily total.
            Also deduplicates nutrition data from multiple sources (e.g. MyFitnessPal).
            """
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            entries = sorted(m["data"], key=lambda x: x.get("date", ""), reverse=True)
            most_recent_date = entries[0]["date"][:10]  # YYYY-MM-DD
            day_entries = [e for e in entries if e.get("date", "")[:10] == most_recent_date]
            vals = [e["qty"] for e in day_entries if e.get("qty") is not None]
            return round(sum(vals), 1) if vals else None

        # ── Sleep ─────────────────────────────────────────────────────────────
        sleep_hours = None
        sleep_deep_minutes = None
        sleep_rem_minutes = None
        sleep_core_minutes = None
        sleep_bedtime = None
        sleep_wake_time = None

        sleep_metric = metrics.get("sleep_analysis")
        if sleep_metric and sleep_metric.get("data"):
            entries = sorted(
                sleep_metric["data"],
                key=lambda x: x.get("date", ""),
                reverse=True,
            )
            s = entries[0]
            total = s.get("totalSleep")
            if total is not None:
                sleep_hours = round(float(total), 2)
            deep = s.get("deep")
            if deep is not None:
                sleep_deep_minutes = round(float(deep) * 60, 1)
            rem = s.get("rem")
            if rem is not None:
                sleep_rem_minutes = round(float(rem) * 60, 1)
            core = s.get("core")
            if core is not None:
                sleep_core_minutes = round(float(core) * 60, 1)
            sleep_bedtime = s.get("sleepStart") or s.get("inBedStart")
            sleep_wake_time = s.get("sleepEnd") or s.get("inBedEnd")

        # ── Workouts (from workouts array if present) ──────────────────────────
        def _qty(val) -> float:
            if val is None:
                return 0.0
            if isinstance(val, list):
                return sum(_qty(item) for item in val)
            if isinstance(val, dict):
                return float(val.get("qty") or val.get("value") or 0)
            return float(val)

        parsed_workouts = []
        for w in workouts:
            duration_sec = _qty(w.get("duration"))
            duration_min = round(duration_sec / 60, 1)
            energy = _qty(w.get("activeEnergyBurned") or w.get("activeEnergy"))
            dist_raw = w.get("distance")
            dist_km = _qty(dist_raw)
            if isinstance(dist_raw, dict) and dist_raw.get("units") == "mi":
                dist_km = round(dist_km * MILES_TO_KM, 2)
            avg_hr = _qty(
                w.get("avgHeartRate")
                or (w.get("heartRate") or {}).get("avg")
            ) or None
            parsed_workouts.append({
                "name": w.get("name", "Unknown"),
                "duration_min": duration_min,
                "distance_km": dist_km,
                "active_energy": round(energy, 0),
                "avg_hr": round(avg_hr, 0) if avg_hr else None,
                "start": w.get("start", ""),
            })

        # ── Distances (minute-level → sum the day) ─────────────────────────────
        walk_mi = latest_day_sum("walking_running_distance")
        walk_km = round(walk_mi * MILES_TO_KM, 2) if walk_mi is not None else None

        cycle_mi = latest_day_sum("cycling_distance")
        cycle_km = round(cycle_mi * MILES_TO_KM, 2) if cycle_mi is not None else None

        # Swimming distance — Health Auto Export uses meters; fall back to miles
        swim_m = latest_day_sum("swimming_distance")
        if swim_m is not None:
            swim_km = round(swim_m / 1000, 2)
        else:
            swim_mi = latest_day_sum("swimming_distance_goal")  # alternative key
            swim_km = round(swim_mi * MILES_TO_KM, 2) if swim_mi is not None else None

        # ── Workout minutes ────────────────────────────────────────────────────
        # Prefer sum of explicit workout durations; fall back to apple_exercise_time
        if parsed_workouts:
            workout_mins = round(sum(w["duration_min"] for w in parsed_workouts), 1)
        else:
            workout_mins = latest_day_sum("apple_exercise_time")
            if workout_mins is None:
                workout_mins = latest_day_sum("exercise_time")

        return cls(
            steps=latest_day_sum("step_count"),
            active_calories=latest_day_sum("active_energy"),
            bmr_calories=latest_day_sum("basal_energy_burned"),
            resting_hr=latest("resting_heart_rate"),
            hrv=latest("heart_rate_variability_sdnn"),
            weight_kg=_weight_as_kg(metrics.get("weight_body_mass")),
            body_fat_pct=latest("body_fat_percentage"),
            sleep_hours=sleep_hours,
            sleep_deep_minutes=sleep_deep_minutes,
            sleep_rem_minutes=sleep_rem_minutes,
            sleep_core_minutes=sleep_core_minutes,
            sleep_bedtime=sleep_bedtime,
            sleep_wake_time=sleep_wake_time,
            workouts=parsed_workouts,
            protein_g=latest_day_sum("protein"),
            carbs_g=latest_day_sum("carbohydrates"),
            fat_g=latest_day_sum("total_fat"),
            calories_consumed=latest_day_sum("dietary_energy"),
            walking_running_distance_km=walk_km,
            cycling_distance_km=cycle_km,
            swimming_distance_km=swim_km,
            workout_minutes=workout_mins,
        )

    def to_summary_dict(self) -> dict:
        return {
            "steps": self.steps,
            "active_calories": self.active_calories,
            "bmr_calories": self.bmr_calories,
            "tdee": self.tdee,
            "resting_hr": self.resting_hr,
            "hrv": self.hrv,
            "weight_lbs": self.weight_lbs,
            "weight_kg": self.weight_kg,
            "body_fat_pct": self.body_fat_pct,
            "sleep_hours": self.sleep_hours,
            "sleep_deep_minutes": self.sleep_deep_minutes,
            "sleep_rem_minutes": self.sleep_rem_minutes,
            "sleep_core_minutes": self.sleep_core_minutes,
            "sleep_bedtime": self.sleep_bedtime,
            "sleep_wake_time": self.sleep_wake_time,
            "workouts": self.workouts,
            "derived_activities": self.derived_activities,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "calories_consumed": self.calories_consumed,
            "walking_running_distance_km": self.walking_running_distance_km,
            "cycling_distance_km": self.cycling_distance_km,
            "swimming_distance_km": self.swimming_distance_km,
            "workout_minutes": self.workout_minutes,
        }

    def to_coaching_string(self) -> str:
        def fmt(label: str, val, unit: str = "", decimals: int = 0) -> str:
            if val is None:
                return f"  {label}: Not logged"
            if decimals > 0:
                return f"  {label}: {val:.{decimals}f}{unit}"
            return f"  {label}: {int(val)}{unit}"

        # Workouts: prefer explicit workout objects, fall back to derived activities
        activity_str = ""
        activities = self.workouts if self.workouts else self.derived_activities
        if activities:
            for a in activities:
                if "duration_min" in a:
                    # Full workout object
                    activity_str += f"\n    - {a['name']}: {a['duration_min']:.0f} min"
                    if a.get("distance_km"):
                        activity_str += f", {a['distance_km']:.1f} km"
                    if a.get("active_energy"):
                        activity_str += f", {a['active_energy']:.0f} kcal"
                    if a.get("avg_hr"):
                        activity_str += f", avg HR {a['avg_hr']:.0f} bpm"
                else:
                    # Derived from distance metric
                    activity_str += f"\n    - {a['name']}: {a['distance_km']:.1f} km"
        else:
            activity_str = "\n    - No activity logged"

        def fmt_time(ts: Optional[str]) -> str:
            if not ts:
                return "Not logged"
            try:
                dt = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%-I:%M %p")
            except Exception:
                return ts[:16]

        return f"""YESTERDAY'S METRICS:
Body:
{fmt('Weight', self.weight_lbs, ' lbs', 1)}
{fmt('Body Fat', self.body_fat_pct, '%', 1)}

Activity:
{fmt('Steps', self.steps)}
{fmt('Active Calories', self.active_calories, ' kcal')}
{fmt('BMR', self.bmr_calories, ' kcal')}
{fmt('TDEE (est)', self.tdee, ' kcal')}
{fmt('Walk/Run Distance', self.walking_running_distance_km, ' km', 2)}
{fmt('Cycling Distance', self.cycling_distance_km, ' km', 2)}
{fmt('Swimming Distance', self.swimming_distance_km, ' km', 2)}
{fmt('Workout Minutes', self.workout_minutes, ' min', 0)}

Workouts/Activity:{activity_str}

Heart:
{fmt('Resting HR', self.resting_hr, ' bpm')}
{fmt('HRV', self.hrv, ' ms', 1)}

Sleep:
{fmt('Total Sleep', self.sleep_hours, ' hrs', 2)}
{fmt('Deep Sleep', self.sleep_deep_minutes, ' min', 1)}
{fmt('Core Sleep', self.sleep_core_minutes, ' min', 1)}
{fmt('REM Sleep', self.sleep_rem_minutes, ' min', 1)}
  Bedtime: {fmt_time(self.sleep_bedtime)}
  Wake: {fmt_time(self.sleep_wake_time)}

Nutrition:
{fmt('Calories Consumed', self.calories_consumed, ' kcal')}
{fmt('Protein', self.protein_g, 'g')}
{fmt('Carbs', self.carbs_g, 'g')}
{fmt('Fat', self.fat_g, 'g')}"""
