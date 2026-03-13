from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

MILES_TO_KM = 1.60934


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

    @classmethod
    def parse(cls, raw_json: dict) -> "HealthData":
        data = raw_json.get("data", raw_json)
        metrics = {m["name"]: m for m in data.get("metrics", [])}
        workouts = data.get("workouts", [])

        def latest(metric_name: str) -> Optional[float]:
            """Return the qty from the most recent entry for a metric."""
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            entries = sorted(m["data"], key=lambda x: x.get("date", ""), reverse=True)
            val = entries[0].get("qty")
            return float(val) if val is not None else None

        def latest_day_sum(metric_name: str) -> Optional[float]:
            """Sum all entries for the most recent date (handles duplicate sources)."""
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            entries = sorted(m["data"], key=lambda x: x.get("date", ""), reverse=True)
            most_recent_date = entries[0]["date"][:10]  # YYYY-MM-DD
            day_entries = [e for e in entries if e.get("date", "")[:10] == most_recent_date]
            vals = [e["qty"] for e in day_entries if e.get("qty") is not None]
            return round(sum(vals), 1) if vals else None

        # ── Sleep ─────────────────────────────────────────────────────────────
        # Health Auto Export exports sleep as one entry per night with fields:
        # totalSleep, deep, rem, core, awake (all in hours), sleepStart, sleepEnd
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

        # ── Workouts ──────────────────────────────────────────────────────────
        # duration: seconds → divide by 60 for minutes
        # activeEnergyBurned: dict {"qty": N, "units": "kcal"} — the total
        # distance: dict {"qty": N, "units": "km"}
        def _qty(val) -> float:
            """Extract numeric qty from plain number, {"qty": N} dict, or sum a list."""
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

            # Prefer the top-level total over the segment array
            energy = _qty(w.get("activeEnergyBurned") or w.get("activeEnergy"))

            dist_raw = w.get("distance")
            dist_km = _qty(dist_raw)
            # Convert miles to km if units say "mi"
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

        # ── Walking/running distance ──────────────────────────────────────────
        # Metric units are "mi" — convert to km
        dist_mi = latest("walking_running_distance")
        dist_km = round(dist_mi * MILES_TO_KM, 2) if dist_mi is not None else None

        return cls(
            steps=latest("step_count"),
            active_calories=latest("active_energy"),
            bmr_calories=latest("basal_energy_burned"),
            resting_hr=latest("resting_heart_rate"),
            hrv=latest("heart_rate_variability_sdnn"),
            weight_kg=latest("weight_body_mass"),
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
            walking_running_distance_km=dist_km,
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
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "calories_consumed": self.calories_consumed,
            "walking_running_distance_km": self.walking_running_distance_km,
        }

    def to_coaching_string(self) -> str:
        def fmt(label: str, val, unit: str = "", decimals: int = 0) -> str:
            if val is None:
                return f"  {label}: Not logged"
            if decimals > 0:
                return f"  {label}: {val:.{decimals}f}{unit}"
            return f"  {label}: {int(val)}{unit}"

        workout_str = ""
        if self.workouts:
            for w in self.workouts:
                workout_str += f"\n    - {w['name']}: {w['duration_min']:.0f} min"
                if w.get("distance_km"):
                    workout_str += f", {w['distance_km']:.1f} km"
                if w.get("active_energy"):
                    workout_str += f", {w['active_energy']:.0f} kcal"
                if w.get("avg_hr"):
                    workout_str += f", avg HR {w['avg_hr']:.0f} bpm"
        else:
            workout_str = "\n    - No workouts logged"

        # Format sleep bedtime/wake nicely
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
{fmt('Walking/Running Distance', self.walking_running_distance_km, ' km', 2)}

Workouts:{workout_str}

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
