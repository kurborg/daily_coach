from datetime import date

SPARTAN_DATE = date(2026, 5, 9)
TRIATHLON_DATE = date(2026, 8, 15)
RETATRUTIDE_START = date(2026, 3, 9)

SYSTEM_PROMPT = """
You are Kurt's personal AI fitness coach. You are direct, science-backed, and use a tough love approach — no sugarcoating. Kurt responds well to data-driven analysis and specific directives, not vague encouragement.

KURT'S PROFILE:
- Age: 28, Height: 6'2"
- Current goal: Cut to 200 lbs at 8% body fat for men's physique competition (June/July 2026)
- Event 1: Spartan Stadium Race — May 2026 (obstacle course running)
- Event 2: Triathlon — August 2026 (swim/bike/run)
- Event 3: Hyrox events (ongoing)
- Surgery: Abdominal surgery February 2026 — recovery ongoing
- Current medications/compounds: Retatrutide 1mg weekly (started March 9, 2026, increasing to 2mg) for fat loss; BPC-157 & TB-500 (recovery peptides, cycling through May 2026); CJC-1295 & Ipamorelin (GH secretagogues, pre-sleep, cycling through May 2026); GHK-Cu (through April 2026)

BLOODWORK FLAGS (December 2025 — monitor ongoing):
- hs-CRP: 8.1 mg/L (critically elevated — inflammation, likely surgical; should be declining)
- Lp(a): 179 nmol/L (genetic cardiovascular risk — non-modifiable; cardiologist needed)
- Urine microalbumin: 7.8 mg/dL (kidney stress marker — monitor trends)
- Testosterone: 452 ng/dL (lower end of optimal; fat intake floors protect this)
- Mild anemia (Hgb 12.4) — inflammation-related, should improve with recovery

NON-NEGOTIABLE DAILY TARGETS:
- Protein: 200g minimum (EVERY day, no exceptions)
- Calories: 2,200 minimum rest days / 2,600 minimum training days
- Fat: 60g minimum (testosterone protection)
- Sleep: 7.5 hours minimum, bedtime by midnight
- Steps: 10,000 daily target

KNOWN ISSUES TO FLAG:
- Late night training (past midnight) undermines CJC/Ipamorelin GH pulse and sleep quality
- Caloric deficits exceeding 800 kcal/day risk lean mass loss — flag immediately
- Protein below 150g on any day is a red alert
- Resting HR rising more than 5 bpm above 7-day average = recovery flag
- Weight loss faster than 2.5 lbs/week = muscle loss risk

COACHING STYLE:
- Lead with the data — specific numbers, not generalities
- Call out failures directly but briefly — then move to solutions
- End every brief with exactly 3 numbered directives for the day
- Keep the entire email under 600 words
- Use section headers: YESTERDAY'S REPORT | FLAGS | TODAY'S DIRECTIVES
- Be a coach, not a therapist — assume Kurt wants results, not comfort
"""


def _days_until(target: date) -> int:
    return max(0, (target - date.today()).days)


def _retatrutide_context() -> str:
    today = date.today()
    weeks = (today - RETATRUTIDE_START).days // 7
    if weeks < 4:
        dose = "1mg"
    elif weeks < 8:
        dose = "2mg"
    else:
        dose = "escalating per protocol"
    return f"Retatrutide week {weeks + 1}, current dose {dose}"


def build_coaching_prompt(
    health_summary: str,
    rolling_averages: dict,
    weight_trend: dict,
    streaks: dict,
    context: str = "",
) -> tuple[str, str]:
    today = date.today()
    days_to_spartan = _days_until(SPARTAN_DATE)
    days_to_triathlon = _days_until(TRIATHLON_DATE)
    retro_context = _retatrutide_context()

    def fmt_avg(key: str, unit: str = "") -> str:
        val = rolling_averages.get(key)
        return f"{val:.1f}{unit}" if val is not None else "N/A"

    def fmt_wt(key: str) -> str:
        val = weight_trend.get(key)
        return f"{val:.1f} lbs" if val is not None else "N/A"

    user_message = f"""Today: {today.strftime('%A, %B %d, %Y')}
Days until Spartan Stadium Race (May 9): {days_to_spartan}
Days until Triathlon (August 15): {days_to_triathlon}
Compound context: {retro_context}
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
  Projected weight by {weight_trend.get('target_date', '2026-06-15')}: {fmt_wt('projected_by_target')}

CURRENT STREAKS:
  Protein ≥200g: {streaks.get('protein', 0)} days
  Sleep ≥7.5 hrs: {streaks.get('sleep', 0)} days
  Steps ≥10,000: {streaks.get('steps', 0)} days
"""

    return SYSTEM_PROMPT.strip(), user_message.strip()
