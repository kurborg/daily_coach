from datetime import date, datetime
from config_loader import get_config


def _days_until(d: date) -> int:
    return max(0, (d - date.today()).days)


def _build_system_prompt(cfg: dict) -> str:
    p = cfg["profile"]
    g = cfg["goals"]
    t = cfg["daily_targets"]
    f = cfg["flags"]
    s = cfg.get("surgery", {})

    # Events
    events_text = "\n".join(
        f"- {e['name']} — {e['date'] or 'ongoing'}"
        for e in cfg["events"]
    )

    # Active compounds
    today = date.today()
    compound_lines = []
    for c in cfg["compounds"]:
        end = c.get("end_date")
        if end and datetime.strptime(end, "%Y-%m-%d").date() < today:
            continue  # cycle ended, skip
        dose = ""
        if c.get("start_date") and c.get("dose_schedule"):
            start = datetime.strptime(c["start_date"], "%Y-%m-%d").date()
            weeks = (today - start).days // 7
            for sched in c["dose_schedule"]:
                if sched["weeks_start"] <= weeks <= sched["weeks_end"]:
                    dose = f" {sched['dose']}"
                    break
        compound_lines.append(f"- {c['name']}{dose}: {c['notes']}")
    compounds_text = "\n".join(compound_lines) if compound_lines else "None currently active"

    # Bloodwork
    bw_lines = [
        f"- {b['marker']}: {b['value']} ({b['flag']})"
        for b in cfg["bloodwork"]
    ]
    bloodwork_text = "\n".join(bw_lines)

    # Surgery
    surgery_text = ""
    if s:
        surgery_text = f"- Surgery: {s['type']} ({s['date']}) — {s['notes']}"

    return f"""You are {p['name']}'s personal AI fitness coach. You are direct, science-backed, and use a tough love approach — no sugarcoating. {p['name']} responds well to data-driven analysis and specific directives, not vague encouragement.

{p['name'].upper()}'S PROFILE:
- Age: {p['age']}, Height: {p['height_ft']}'{p['height_in']}"
- Current goal: Cut to {g['weight_target_lbs']} lbs at {g['body_fat_target_pct']}% body fat by {g['weight_cutoff_date']}
- Events:
{events_text}
{surgery_text}
- Current compounds:
{compounds_text}

BLOODWORK FLAGS (monitor ongoing):
{bloodwork_text}

NON-NEGOTIABLE DAILY TARGETS:
- Protein: {t['protein_g']}g minimum (EVERY day, no exceptions)
- Calories: {t['calories_rest_day']} kcal minimum rest days / {t['calories_training_day']} kcal minimum training days
- Fat: {t['fat_g_min']}g minimum (testosterone protection)
- Sleep: {t['sleep_hours']} hours minimum, bedtime by midnight
- Steps: {t['steps']:,} daily target

KNOWN ISSUES TO FLAG:
- Late night training (past midnight) undermines CJC/Ipamorelin GH pulse and sleep quality
- Caloric deficits exceeding {f['max_daily_deficit_kcal']} kcal/day risk lean mass loss — flag immediately
- Protein below {f['protein_red_alert_g']}g on any day is a red alert
- Resting HR rising more than {f['hr_spike_bpm_above_avg']} bpm above 7-day average = recovery flag
- Weight loss faster than {f['max_weekly_weight_loss_lbs']} lbs/week = muscle loss risk

COACHING STYLE:
- Lead with the data — specific numbers, not generalities
- Call out failures directly but briefly — then move to solutions
- End every brief with exactly 3 numbered directives for the day
- Keep the entire email under 600 words
- Use section headers: YESTERDAY'S REPORT | FLAGS | TODAY'S DIRECTIVES
- Be a coach, not a therapist — assume {p['name']} wants results, not comfort

FORMATTING RULES (strictly enforced):
- Do NOT use any markdown syntax whatsoever — no #, ##, **, *, --, ___, backticks, or any other markdown
- Section headers must be plain text exactly as specified: YESTERDAY'S REPORT, FLAGS, TODAY'S DIRECTIVES
- Directives must be plain numbered lines: 1. text, 2. text, 3. text
- No bullet points with dashes or asterisks — use plain sentences
- No bold, italic, or any other text decoration"""


def _retatrutide_context(cfg: dict) -> str:
    for c in cfg["compounds"]:
        if "retatrutide" in c["name"].lower() and c.get("start_date"):
            start = datetime.strptime(c["start_date"], "%Y-%m-%d").date()
            weeks = (date.today() - start).days // 7
            dose = "unknown dose"
            for sched in c.get("dose_schedule", []):
                if sched["weeks_start"] <= weeks <= sched["weeks_end"]:
                    dose = sched["dose"]
                    break
            return f"Retatrutide week {weeks + 1}, current dose {dose}"
    return ""


def build_coaching_prompt(
    health_summary: str,
    rolling_averages: dict,
    weight_trend: dict,
    streaks: dict,
    context: str = "",
) -> tuple[str, str]:
    cfg = get_config()
    t = cfg["daily_targets"]
    g = cfg["goals"]
    today = date.today()

    system_prompt = _build_system_prompt(cfg)
    retro_context = _retatrutide_context(cfg)

    # Event countdowns
    event_lines = []
    for e in cfg["events"]:
        if e["date"]:
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            event_lines.append(f"Days until {e['name']}: {_days_until(d)}")
        else:
            event_lines.append(f"{e['name']}: ongoing")
    events_str = "\n".join(event_lines)

    def fmt_avg(key: str, unit: str = "") -> str:
        val = rolling_averages.get(key)
        return f"{val:.1f}{unit}" if val is not None else "N/A"

    def fmt_wt(key: str) -> str:
        val = weight_trend.get(key)
        return f"{val:.1f} lbs" if val is not None else "N/A"

    user_message = f"""Today: {today.strftime('%A, %B %d, %Y')}
{events_str}
{f'Compound context: {retro_context}' if retro_context else ''}
{f'Additional context: {context}' if context else ''}

{health_summary}

7-DAY ROLLING AVERAGES:
  Steps: {fmt_avg('steps')}
  Active Calories: {fmt_avg('active_calories', ' kcal')}
  Resting HR: {fmt_avg('resting_hr', ' bpm')}
  Sleep: {fmt_avg('sleep_hours', ' hrs')}
  Protein: {fmt_avg('protein_g', 'g')}
  Calories Consumed: {fmt_avg('calories_consumed', ' kcal')}
  Weight: {fmt_avg('weight_lbs', ' lbs')}

WEIGHT TREND:
  Current: {fmt_wt('current')}
  7 days ago: {fmt_wt('week_ago')}
  30 days ago: {fmt_wt('month_ago')}
  Lost this week: {f"{weight_trend.get('lbs_lost_week', 0):.1f} lbs" if weight_trend.get('lbs_lost_week') is not None else 'N/A'}
  Lost this month: {f"{weight_trend.get('lbs_lost_month', 0):.1f} lbs" if weight_trend.get('lbs_lost_month') is not None else 'N/A'}
  Projected weight by {g['weight_cutoff_date']}: {fmt_wt('projected_by_target')}

CURRENT STREAKS:
  Protein ≥{t['protein_g']}g: {streaks.get('protein', 0)} days
  Sleep ≥{t['sleep_hours']}hrs: {streaks.get('sleep', 0)} days
  Steps ≥{t['steps']:,}: {streaks.get('steps', 0)} days"""

    return system_prompt.strip(), user_message.strip()
