import argparse
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

from config_loader import load_all_users, load_user, resolve_ref
from drive_client import get_latest_health_export, get_latest_workout_export
from health_parser import HealthData
from trend_tracker import save_daily_summary, get_rolling_averages, get_weight_trend, get_streak
from coach_prompt import build_coaching_prompt, build_review_prompt
from anthropic_client import get_coaching_brief
from email_client import send_coaching_email, send_review_email


def run_for_user(cfg: dict, dry_run: bool = False):
    user_id = cfg["_user_id"]
    name = cfg["profile"]["name"]
    today_str = date.today().isoformat()
    date_str = date.today().strftime("%A, %B %d, %Y")

    print(f"[Coach] ── {name} ──────────────────────────")

    # 1. Fetch health data
    raw_json = get_latest_health_export(
        folder_id=cfg.get("folder_id", ""),
        folder_name=cfg.get("folder_name", ""),
    )

    # 1b. Fetch workouts from separate folder and inject if configured
    if cfg.get("workout_folder_name") or cfg.get("workout_folder_id"):
        workouts = get_latest_workout_export(
            folder_id=cfg.get("workout_folder_id", ""),
            folder_name=cfg.get("workout_folder_name", ""),
        )
        if workouts:
            raw_json["data"]["workouts"] = workouts
            print(f"[Coach] Injected {len(workouts)} workout(s) from workout folder")

    # 2. Parse — always report on yesterday's complete data
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    health = HealthData.parse(raw_json, target_date=yesterday)
    summary_dict = health.to_summary_dict()
    coaching_str = health.to_coaching_string()

    # 3. Save history
    save_daily_summary(today_str, summary_dict, user_id=user_id)

    # 4. Rolling averages
    rolling_avgs = get_rolling_averages(user_id=user_id, days=7)

    # 5. Weight trend
    weight_trend = get_weight_trend(user_id=user_id, cfg=cfg)

    # 6. Streaks — driven by cfg["streaks"]
    streaks = {}
    for s in cfg.get("streaks", []):
        target = resolve_ref(cfg, s["target_ref"])
        streaks[s["metric"]] = get_streak(
            s["metric"], target,
            user_id=user_id,
            higher_is_better=s.get("higher_is_better", True),
        )

    # 7. Build prompt
    system_prompt, user_message = build_coaching_prompt(
        health_summary=coaching_str,
        rolling_averages=rolling_avgs,
        weight_trend=weight_trend,
        streaks=streaks,
        cfg=cfg,
    )

    # 8. Call Claude
    print(f"[Coach] Requesting brief from Claude...")
    coaching_brief = get_coaching_brief(system_prompt, user_message)

    if dry_run:
        print("\n" + "=" * 60)
        print(f"DRY RUN — {name} — {date_str}")
        print("=" * 60)
        print(coaching_brief)
        print("=" * 60)
        return

    # 9. Send email
    send_coaching_email(
        coaching_brief_text=coaching_brief,
        date_str=date_str,
        metrics_summary=summary_dict,
        to_email=cfg["email"],
        cfg=cfg,
    )
    print(f"[Coach] ✓ Done — {name}")


def run_review_for_user(cfg: dict, dry_run: bool = False):
    user_id  = cfg["_user_id"]
    name     = cfg["profile"]["name"]
    today    = date.today()
    today_str = today.isoformat()
    date_str  = today.strftime("%A, %B %d, %Y")

    print(f"[Review] ── {name} ──────────────────────────")

    # Fetch health data
    raw_json = get_latest_health_export(
        folder_id=cfg.get("folder_id", ""),
        folder_name=cfg.get("folder_name", ""),
    )

    if cfg.get("workout_folder_name") or cfg.get("workout_folder_id"):
        workouts = get_latest_workout_export(
            folder_id=cfg.get("workout_folder_id", ""),
            folder_name=cfg.get("workout_folder_name", ""),
        )
        if workouts:
            raw_json["data"]["workouts"] = workouts

    # Parse today's data (not yesterday's)
    health = HealthData.parse(raw_json, target_date=today_str)
    summary_dict = health.to_summary_dict()
    coaching_str = health.to_coaching_string()

    # Claude analysis
    system_prompt, user_message = build_review_prompt(
        health_summary=coaching_str,
        cfg=cfg,
    )
    print(f"[Review] Requesting end-of-day analysis from Claude...")
    review_brief = get_coaching_brief(system_prompt, user_message)

    if dry_run:
        print("\n" + "=" * 60)
        print(f"DRY RUN (review) — {name} — {date_str}")
        print("=" * 60)
        print(review_brief)
        print("=" * 60)
        return

    send_review_email(
        date_str=date_str,
        metrics_summary=summary_dict,
        review_brief_text=review_brief,
        to_email=cfg["email"],
        cfg=cfg,
    )
    print(f"[Review] ✓ Done — {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--user", help="Run for a single user_id only")
    parser.add_argument("--review", action="store_true", help="Send evening day-in-review email instead of morning coaching brief")
    args = parser.parse_args()

    today_str = date.today().isoformat()
    mode = "review" if args.review else "coaching"
    print(f"[Coach] Starting daily {mode} pipeline for {today_str}")

    if args.user:
        users = [load_user(args.user)]
    else:
        users = load_all_users()

    print(f"[Coach] {len(users)} user(s) to process")

    runner = run_review_for_user if args.review else run_for_user

    for cfg in users:
        try:
            runner(cfg, dry_run=args.dry_run)
        except Exception as e:
            print(f"[Coach] ERROR for {cfg.get('profile', {}).get('name', cfg['_user_id'])}: {e}")
            import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
