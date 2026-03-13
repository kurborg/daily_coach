from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


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
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            entries = sorted(m["data"], key=lambda x: x.get("date", ""), reverse=True)
            val = entries[0].get("qty")
            return float(val) if val is not None else None

        def sum_metric(metric_name: str) -> Optional[float]:
            m = metrics.get(metric_name)
            if not m or not m.get("data"):
                return None
            vals = [e.get("qty") for e in m["data"] if e.get("qty") is not None]
            return sum(vals) if vals else None

        # Sleep parsing
        sleep_hours = None
        sleep_deep_minutes = None
        sleep_rem_minutes = None
        sleep_bedtime = None
        sleep_wake_time = None

        sleep_metric = metrics.get("sleep_analysis") or metrics.get("sleepAnalysis")
        if sleep_metric and sleep_metric.get("data"):
            total_sleep_sec = 0
            deep_sec = 0
            rem_sec = 0
            bedtimes = []
            waketimes = []
            for entry in sleep_metric["data"]:
                stage = entry.get("value", entry.get("state", "")).lower()
                qty = entry.get("qty", 0) or 0
                total_sleep_sec += qty
                if "deep" in stage or "slow_wave" in stage:
                    deep_sec += qty
                elif "rem" in stage:
                    rem_sec += qty
                start = entry.get("startDate") or entry.get("start")
                end = entry.get("endDate") or entry.get("end")
                if start:
                    bedtimes.append(start)
                if end:
                    waketimes.append(end)
            if total_sleep_sec > 0:
                sleep_hours = round(total_sleep_sec / 3600, 2)
                sleep_deep_minutes = round(deep_sec / 60, 1)
                sleep_rem_minutes = round(rem_sec / 60, 1)
            if bedtimes:
                sleep_bedtime = min(bedtimes)
            if waketimes:
                sleep_wake_time = max(waketimes)

        # Parse workouts
        parsed_workouts = []
        for w in workouts:
            parsed_workouts.append({
                "name": w.get("name", "Unknown"),
                "duration_min": w.get("duration", 0),
                "distance_km": w.get("distance", 0),
                "active_energy": w.get("activeEnergy", w.get("activeEnergyBurned", 0)),
                "start": w.get("start", w.get("startDate", "")),
            })

        return cls(
            steps=latest("step_count") or latest("stepCount"),
            active_calories=latest("active_energy") or latest("activeEnergyBurned") or sum_metric("active_energy"),
            bmr_calories=latest("basal_energy_burned") or latest("basalEnergyBurned"),
            resting_hr=latest("resting_heart_rate") or latest("restingHeartRate"),
            hrv=latest("heart_rate_variability_sdnn") or latest("heartRateVariabilitySDNN"),
            weight_kg=latest("body_mass") or latest("bodyMass"),
            body_fat_pct=latest("body_fat_percentage") or latest("bodyFatPercentage"),
            sleep_hours=sleep_hours,
            sleep_deep_minutes=sleep_deep_minutes,
            sleep_rem_minutes=sleep_rem_minutes,
            sleep_bedtime=sleep_bedtime,
            sleep_wake_time=sleep_wake_time,
            workouts=parsed_workouts,
            protein_g=sum_metric("dietary_protein") or sum_metric("dietaryProtein"),
            carbs_g=sum_metric("dietary_carbohydrates") or sum_metric("dietaryCarbohydrates"),
            fat_g=sum_metric("dietary_fat_total") or sum_metric("dietaryFatTotal"),
            calories_consumed=sum_metric("dietary_energy_consumed") or sum_metric("dietaryEnergyConsumed"),
            walking_running_distance_km=latest("distance_walking_running") or latest("distanceWalkingRunning"),
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
                if w.get('distance_km'):
                    workout_str += f", {w['distance_km']:.1f} km"
                if w.get('active_energy'):
                    workout_str += f", {w['active_energy']:.0f} kcal"
        else:
            workout_str = "\n    - No workouts logged"

        return f"""YESTERDAY'S METRICS:
Body:
{fmt('Weight', self.weight_lbs, ' lbs', 1)}
{fmt('Body Fat', self.body_fat_pct, '%', 1)}

Activity:
{fmt('Steps', self.steps)}
{fmt('Active Calories', self.active_calories, ' kcal')}
{fmt('BMR', self.bmr_calories, ' kcal')}
{fmt('TDEE (est)', self.tdee, ' kcal')}
{fmt('Walking/Running Distance', self.walking_running_distance_km, ' km', 1)}

Workouts:{workout_str}

Heart:
{fmt('Resting HR', self.resting_hr, ' bpm')}
{fmt('HRV', self.hrv, ' ms', 1)}

Sleep:
{fmt('Total Sleep', self.sleep_hours, ' hrs', 2)}
{fmt('Deep Sleep', self.sleep_deep_minutes, ' min')}
{fmt('REM Sleep', self.sleep_rem_minutes, ' min')}
  Bedtime: {self.sleep_bedtime or 'Not logged'}
  Wake: {self.sleep_wake_time or 'Not logged'}

Nutrition:
{fmt('Calories Consumed', self.calories_consumed, ' kcal')}
{fmt('Protein', self.protein_g, 'g')}
{fmt('Carbs', self.carbs_g, 'g')}
{fmt('Fat', self.fat_g, 'g')}"""
