import argparse
import sys
from datetime import date
from dotenv import load_dotenv

load_dotenv()

from drive_client import get_latest_health_export
from health_parser import HealthData
from trend_tracker import save_daily_summary, get_rolling_averages, get_weight_trend, get_streak
from coach_prompt import build_coaching_prompt
from anthropic_client import get_coaching_brief
from email_client import send_coaching_email


def run_daily_coaching(dry_run: bool = False):
    today_str = date.today().isoformat()
    print(f"[Coach] Starting daily coaching pipeline for {today_str}")

    # 1. Fetch latest health export from Google Drive
    print("[Coach] Fetching health export from Google Drive...")
    raw_json = get_latest_health_export()

    # 2. Parse into HealthData
    print("[Coach] Parsing health data...")
    health = HealthData.parse(raw_json)
    summary_dict = health.to_summary_dict()
    coaching_str = health.to_coaching_string()

    # 3. Save today's summary to history
    save_daily_summary(today_str, summary_dict)

    # 4. Get rolling averages
    rolling_avgs = get_rolling_averages(days=7)

    # 5. Get weight trend
    weight_trend = get_weight_trend()

    # 6. Get streaks
    streaks = {
        "protein": get_streak("protein_g", 200, higher_is_better=True),
        "sleep": get_streak("sleep_hours", 7.5, higher_is_better=True),
        "steps": get_streak("steps", 10000, higher_is_better=True),
    }

    # 7. Calculate retatrutide context (done inside coach_prompt)
    context = ""

    # 8. Build coaching prompt
    system_prompt, user_message = build_coaching_prompt(
        health_summary=coaching_str,
        rolling_averages=rolling_avgs,
        weight_trend=weight_trend,
        streaks=streaks,
        context=context,
    )

    # 9. Call Claude API
    print("[Coach] Requesting coaching brief from Claude...")
    coaching_brief = get_coaching_brief(system_prompt, user_message)

    date_str = date.today().strftime("%A, %B %d, %Y")

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN — Email would be sent with this content:")
        print("=" * 60)
        print(f"Subject: Daily Coaching Brief — {date_str}")
        print()
        print(coaching_brief)
        print("=" * 60)
        return

    # 10. Send email
    print("[Coach] Sending coaching email...")
    send_coaching_email(
        coaching_brief_text=coaching_brief,
        date_str=date_str,
        metrics_summary=summary_dict,
    )

    print(f"[Coach] ✓ Done — {date_str}")


def main():
    parser = argparse.ArgumentParser(description="AI Fitness Coach — Daily Coaching Pipeline")
    parser.add_argument("--test", action="store_true", help="Run pipeline once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline but print email instead of sending")
    args = parser.parse_args()

    if args.dry_run:
        run_daily_coaching(dry_run=True)
    else:
        run_daily_coaching(dry_run=False)


if __name__ == "__main__":
    main()
