from datetime import date, datetime
from config_loader import resolve_ref


def _days_until(d: date) -> int:
    return max(0, (d - date.today()).days)


def _build_system_prompt(cfg: dict) -> str:
    p = cfg["profile"]
    g = cfg.get("goals", {})
    t = cfg.get("daily_targets", {})
    f = cfg.get("flags", {})
    s = cfg.get("surgery", {})

    goal_type = cfg.get("goal_type", "cut")
    coaching_style_key = cfg.get("coaching_style", "tough_love")
    coaching_focus = cfg.get("coaching_focus", "")

    # ── Coaching style ────────────────────────────────────────────────────────
    style_text = {
        "tough_love": (
            f"You are direct, science-backed, and use a tough love approach — no sugarcoating. "
            f"{p['name']} responds well to data-driven analysis and specific directives, not vague encouragement."
        ),
        "supportive": (
            f"You are encouraging, science-backed, and lead with wins before gaps. "
            f"{p['name']} responds well to positive reinforcement paired with clear, actionable guidance. "
            f"Celebrate consistency and progress; be direct about gaps without being harsh."
        ),
        "data_only": (
            f"You are a precision data coach. Lead with numbers, skip the editorial. "
            f"State what happened, flag deviations from targets, give directives. Minimal commentary."
        ),
    }.get(coaching_style_key, "")

    # ── Goal framing ──────────────────────────────────────────────────────────
    if goal_type == "cut":
        goal_str = "Cut"
        if g.get("weight_target_lbs"):
            goal_str += f" to {g['weight_target_lbs']} lbs"
        if g.get("body_fat_target_pct"):
            goal_str += f" at {g['body_fat_target_pct']}% body fat"
        if g.get("weight_cutoff_date"):
            goal_str += f" by {g['weight_cutoff_date']}"
    elif goal_type == "bulk":
        goal_str = "Lean bulk — maximize muscle gain with controlled caloric surplus"
        if g.get("weight_target_lbs"):
            goal_str += f", targeting {g['weight_target_lbs']} lbs"
    elif goal_type == "maintain":
        goal_str = "Body recomposition — hold weight steady while improving body composition"
    elif goal_type == "active":
        goal_str = "Build healthy habits — increase daily activity, improve energy and consistency"
    elif goal_type == "performance":
        goal_str = "Event performance — nutrition and recovery serve training output above all else"
    elif goal_type == "aesthetics":
        goal_str = "Aesthetics-first physique — maximize definition, muscle retention, and visual symmetry"
        if g.get("body_fat_target_pct"):
            goal_str += f", targeting {g['body_fat_target_pct']}% BF"
    else:
        goal_str = "General fitness improvement"

    # ── Goal directive ────────────────────────────────────────────────────────
    goal_directive = {
        "cut": (
            "Prioritize protein adequacy and deficit management. Flag any day calories drop too low "
            "or protein is missed. Muscle retention is non-negotiable — weight loss must not come at "
            "the cost of lean mass."
        ),
        "bulk": (
            "Prioritize hitting calorie surplus and protein targets every day. Flag missed surpluses "
            "or drops in training volume. A surplus not eaten is growth not realized."
        ),
        "maintain": (
            "Small deficit or surplus swings are acceptable. Consistency in training and protein "
            "is the primary success metric. Flag any multi-day trend in the wrong direction."
        ),
        "active": (
            "Focus on steps, sleep, and habit streaks above all else. Celebrate consistency. "
            "Be encouraging about progress — this person is building a foundation, not chasing extremes."
        ),
        "performance": (
            "Training quality and recovery readiness are the primary outputs. Flag anything that "
            "compromises training capacity — poor sleep, undereating, elevated resting HR."
        ),
        "aesthetics": (
            "Every flag must reference body composition impact. Muscle loss risk is the highest-priority "
            "alert. Scale weight matters less than the body composition trend. Emphasize the behaviors "
            "that directly drive definition and muscle retention."
        ),
    }.get(goal_type, "Drive consistent progress toward the stated goal.")

    # ── Events / milestones ───────────────────────────────────────────────────
    events_section = ""
    if cfg.get("events"):
        event_lines = "\n".join(
            f"  - {e['name']} — {e['date'] or 'ongoing'}"
            for e in cfg["events"]
        )
        events_section = f"\n- Milestones / Events:\n{event_lines}"

    # ── Surgery ───────────────────────────────────────────────────────────────
    surgery_section = ""
    if s:
        surgery_section = f"\n- Surgery: {s['type']} ({s['date']}) — {s['notes']}"

    # ── Active compounds ──────────────────────────────────────────────────────
    compounds_section = ""
    active_compounds = []  # list of (name, dose, notes)
    if cfg.get("compounds"):
        today = date.today()
        for c in cfg["compounds"]:
            end = c.get("end_date")
            if end and datetime.strptime(end, "%Y-%m-%d").date() < today:
                continue
            dose = ""
            if c.get("start_date") and c.get("dose_schedule"):
                start = datetime.strptime(c["start_date"], "%Y-%m-%d").date()
                weeks = (today - start).days // 7
                for sched in c["dose_schedule"]:
                    if sched["weeks_start"] <= weeks <= sched["weeks_end"]:
                        dose = f" {sched['dose']}"
                        break
            active_compounds.append((c["name"], dose, c.get("notes", "")))
        if active_compounds:
            lines = "\n".join(f"  - {name}{dose}: {notes}" for name, dose, notes in active_compounds)
            compounds_section = f"\n- Current compounds:\n{lines}"

    # ── Bloodwork ─────────────────────────────────────────────────────────────
    bloodwork_section = ""
    if cfg.get("bloodwork"):
        bw_lines = "\n".join(
            f"- {b['marker']}: {b['value']} ({b['flag']})"
            for b in cfg["bloodwork"]
        )
        bloodwork_section = f"\nBLOODWORK FLAGS (monitor ongoing):\n{bw_lines}\n"

    # ── Daily targets — only include configured fields ─────────────────────────
    target_lines = []
    if t.get("protein_g"):
        target_lines.append(f"- Protein: {t['protein_g']}g minimum (EVERY day, no exceptions)")
    if t.get("calories_rest_day") and t.get("calories_training_day"):
        target_lines.append(f"- Calories: {t['calories_rest_day']} kcal rest days / {t['calories_training_day']} kcal training days")
    elif t.get("calories_rest_day"):
        target_lines.append(f"- Calories: {t['calories_rest_day']} kcal daily")
    elif t.get("calories_training_day"):
        target_lines.append(f"- Calories: {t['calories_training_day']} kcal on training days")
    if t.get("fat_g_min"):
        target_lines.append(f"- Fat: {t['fat_g_min']}g minimum (hormone support)")
    if t.get("sleep_hours"):
        target_lines.append(f"- Sleep: {t['sleep_hours']} hours minimum")
    if t.get("steps"):
        target_lines.append(f"- Steps: {t['steps']:,} daily target")
    if t.get("cardio_mi"):
        target_lines.append(f"- Cardio: {t['cardio_mi']} miles daily")
    if t.get("workout_minutes"):
        target_lines.append(f"- Training: {t['workout_minutes']} minutes minimum")
    targets_text = "\n".join(target_lines) if target_lines else "- No specific daily targets configured"

    # ── Known issues — dynamically built from flags + active compounds ─────────
    issue_lines = []
    if f.get("max_daily_deficit_kcal"):
        issue_lines.append(f"- Caloric deficits exceeding {f['max_daily_deficit_kcal']} kcal/day risk lean mass loss — flag immediately")
    if f.get("protein_red_alert_g"):
        issue_lines.append(f"- Protein below {f['protein_red_alert_g']}g on any day is a red alert")
    if f.get("hr_spike_bpm_above_avg"):
        issue_lines.append(f"- Resting HR rising more than {f['hr_spike_bpm_above_avg']} bpm above 7-day average = recovery flag")
    if f.get("max_weekly_weight_loss_lbs"):
        issue_lines.append(f"- Weight loss faster than {f['max_weekly_weight_loss_lbs']} lbs/week = muscle loss risk")
    if f.get("late_training_cutoff_hour"):
        gh_names = [
            name for name, _, _ in active_compounds
            if any(kw in name.lower() for kw in ["cjc", "ipamorelin", "ghrp", "ghrh", "sermorelin"])
        ]
        if gh_names:
            issue_lines.append(
                f"- Late night training (past {f['late_training_cutoff_hour']}:00) undermines "
                f"{', '.join(gh_names)} GH pulse and sleep quality"
            )
        else:
            issue_lines.append(f"- Late night training (past {f['late_training_cutoff_hour']}:00) undermines sleep quality and recovery")

    issues_section = ""
    if issue_lines:
        issues_section = "\nKNOWN ISSUES TO FLAG:\n" + "\n".join(issue_lines) + "\n"

    # ── Coaching focus — placed after goal directive so it explicitly overrides ─
    focus_block = (
        f"\nPRIMARY PRIORITY (overrides generic goal guidance — apply this lens to every insight and directive):\n{coaching_focus}\n"
        if coaching_focus else ""
    )

    return f"""You are {p['name']}'s personal AI fitness coach. {style_text}

{p['name'].upper()}'S PROFILE:
- Age: {p['age']}, Height: {p['height_ft']}'{p['height_in']}"
- Goal: {goal_str}{events_section}{surgery_section}{compounds_section}

GOAL DIRECTIVE:
{goal_directive}
{focus_block}{bloodwork_section}
NON-NEGOTIABLE DAILY TARGETS:
{targets_text}
{issues_section}
COACHING STYLE:
- Lead with the data — specific numbers, not generalities
- Call out failures directly but briefly — then move to solutions
- End every brief with exactly 3 numbered directives for the day
- Keep the entire email under 600 words
- Use section headers: YESTERDAY'S REPORT | FLAGS | TODAY'S DIRECTIVES
- Be a coach, not a therapist — assume {p['name']} wants results, not comfort
{f"- Every insight and directive must be filtered through the PRIMARY PRIORITY above" if coaching_focus else ""}

FORMATTING RULES (strictly enforced):
- Do NOT use any markdown syntax whatsoever — no #, ##, **, *, --, ___, backticks, or any other markdown
- Section headers must be plain text exactly as specified: YESTERDAY'S REPORT, FLAGS, TODAY'S DIRECTIVES
- Directives must be plain numbered lines: 1. text, 2. text, 3. text
- No bullet points with dashes or asterisks — use plain sentences
- No bold, italic, or any other text decoration"""


def _retatrutide_context(cfg: dict) -> str:
    for c in cfg.get("compounds", []):
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


def build_review_prompt(
    health_summary: str,
    cfg: dict,
) -> tuple[str, str]:
    """Build system + user prompt for the evening day-in-review Claude call."""
    today = date.today()
    t = cfg.get("daily_targets", {})
    g = cfg.get("goals", {})
    p = cfg["profile"]

    # Reuse the same system prompt — all user context is already there.
    # Override just the coaching style instructions for an end-of-day tone.
    system_prompt = _build_system_prompt(cfg)
    # Append evening-specific instruction override
    system_prompt += f"""

EVENING REVIEW MODE:
You are analyzing {p['name']}'s completed day, not planning tomorrow. Your job is:
- Objectively score today against the targets above
- Call out the biggest win and the biggest gap, with specific numbers
- Give 3 directives: 1 for tonight (recovery, sleep prep, final nutrition), 2 for tomorrow
- Use section headers: TODAY'S ANALYSIS | WINS & GAPS | TONIGHT + TOMORROW
- Keep it under 400 words — this is a recap, not a full brief"""

    retro_context = _retatrutide_context(cfg)

    user_message = f"""Today: {today.strftime('%A, %B %d, %Y')} — End-of-Day Review
{f'Compound context: {retro_context}' if retro_context else ''}

{health_summary}

DAILY TARGETS FOR COMPARISON:
{f"- Protein target: {t['protein_g']}g" if t.get('protein_g') else ''}
{f"- Calorie target: {t.get('calories_training_day') if health_summary and 'workout' in health_summary.lower() else t.get('calories_rest_day')} kcal" if t.get('calories_rest_day') or t.get('calories_training_day') else ''}
{f"- Steps target: {t['steps']:,}" if t.get('steps') else ''}
{f"- Sleep target: {t['sleep_hours']} hrs" if t.get('sleep_hours') else ''}
{f"- Weight target: {g['weight_target_lbs']} lbs by {g['weight_cutoff_date']}" if g.get('weight_target_lbs') and g.get('weight_cutoff_date') else ''}

Analyze today. Be direct. No filler."""

    return system_prompt.strip(), user_message.strip()


def build_coaching_prompt(
    health_summary: str,
    rolling_averages: dict,
    weight_trend: dict,
    streaks: dict,
    cfg: dict,
    context: str = "",
) -> tuple[str, str]:
    t = cfg.get("daily_targets", {})
    g = cfg.get("goals", {})
    today = date.today()

    system_prompt = _build_system_prompt(cfg)
    retro_context = _retatrutide_context(cfg)

    # Event countdowns
    event_lines = []
    for e in cfg.get("events", []):
        if e["date"]:
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            event_lines.append(f"Days until {e['name']}: {_days_until(d)}")
        else:
            event_lines.append(f"{e['name']}: ongoing")
    events_str = "\n".join(event_lines) if event_lines else ""

    def fmt_avg(key: str, unit: str = "") -> str:
        val = rolling_averages.get(key)
        return f"{val:.1f}{unit}" if val is not None else "N/A"

    def fmt_wt(key: str) -> str:
        val = weight_trend.get(key)
        return f"{val:.1f} lbs" if val is not None else "N/A"

    # Build streak lines from cfg["streaks"]
    streak_lines = []
    for s in cfg.get("streaks", []):
        target = resolve_ref(cfg, s["target_ref"])
        count = streaks.get(s["metric"], 0)
        unit = s.get("unit", "")
        label = s["label"]
        streak_lines.append(f"  {label} ≥{target}{unit}: {count} days")
    streaks_str = "\n".join(streak_lines) if streak_lines else "  No streak targets configured"

    # Weight trend — projection line only if cutoff date is configured
    weight_section = f"""WEIGHT TREND:
  Current: {fmt_wt('current')}
  7 days ago: {fmt_wt('week_ago')}
  30 days ago: {fmt_wt('month_ago')}
  Lost this week: {f"{weight_trend.get('lbs_lost_week', 0):.1f} lbs" if weight_trend.get('lbs_lost_week') is not None else 'N/A'}
  Lost this month: {f"{weight_trend.get('lbs_lost_month', 0):.1f} lbs" if weight_trend.get('lbs_lost_month') is not None else 'N/A'}"""
    if g.get("weight_cutoff_date") and weight_trend.get("projected_by_target") is not None:
        weight_section += f"\n  Projected weight by {g['weight_cutoff_date']}: {fmt_wt('projected_by_target')}"

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

{weight_section}

CURRENT STREAKS:
{streaks_str}"""

    return system_prompt.strip(), user_message.strip()
