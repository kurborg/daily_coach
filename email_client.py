import os
from datetime import date
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SPARTAN_DATE = date(2026, 5, 9)
TRIATHLON_DATE = date(2026, 8, 15)

COLORS = {
    "bg": "#1a1a2e",
    "card": "#16213e",
    "accent": "#00d4ff",
    "text": "#e0e0e0",
    "green": "#00c851",
    "red": "#ff4444",
    "muted": "#888888",
}


def _days_until(target: date) -> int:
    return max(0, (target - date.today()).days)


def format_metric_indicator(
    value,
    target: float,
    unit: str,
    higher_is_better: bool = True,
    label: str = "",
) -> str:
    if value is None:
        return f'<span style="color:{COLORS["muted"]}">{label}: N/A</span>'

    on_target = (value >= target) if higher_is_better else (value <= target)
    color = COLORS["green"] if on_target else COLORS["red"]
    icon = "✅" if on_target else "❌"

    display = f"{int(value)}" if unit in ("g", " bpm", "") else f"{value:.1f}"
    return f'<span style="color:{color}">{icon} {label}: {display}{unit}</span>'


def _build_html(
    coaching_brief_text: str,
    date_str: str,
    metrics_summary: dict,
) -> str:
    days_to_spartan = _days_until(SPARTAN_DATE)
    days_to_triathlon = _days_until(TRIATHLON_DATE)

    weight_ind = format_metric_indicator(
        metrics_summary.get("weight_lbs"), 210, " lbs", higher_is_better=False, label="Weight"
    )
    steps_ind = format_metric_indicator(
        metrics_summary.get("steps"), 10000, "", label="Steps"
    )
    sleep_ind = format_metric_indicator(
        metrics_summary.get("sleep_hours"), 7.5, " hrs", label="Sleep"
    )
    protein_ind = format_metric_indicator(
        metrics_summary.get("protein_g"), 200, "g", label="Protein"
    )
    cal_ind = format_metric_indicator(
        metrics_summary.get("active_calories"), 400, " kcal", label="Active Cal"
    )

    brief_html = coaching_brief_text.replace("\n\n", "</p><p>").replace("\n", "<br>")
    brief_html = f"<p>{brief_html}</p>"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Coaching Brief</title>
</head>
<body style="background:{COLORS['bg']};color:{COLORS['text']};font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:20px;">
  <div style="max-width:680px;margin:0 auto;">

    <!-- Header -->
    <div style="background:{COLORS['card']};border-radius:12px;padding:24px;margin-bottom:16px;border-left:4px solid {COLORS['accent']};">
      <h1 style="margin:0;color:{COLORS['accent']};font-size:22px;">DAILY COACHING BRIEF</h1>
      <p style="margin:6px 0 0;color:{COLORS['muted']};font-size:14px;">{date_str}</p>
    </div>

    <!-- Metrics Bar -->
    <div style="background:{COLORS['card']};border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="margin:0 0 14px;font-size:13px;letter-spacing:1px;color:{COLORS['muted']};text-transform:uppercase;">Yesterday at a Glance</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;font-size:13px;line-height:1.8;">
        <div>{weight_ind}</div>
        <div>{steps_ind}</div>
        <div>{sleep_ind}</div>
        <div>{protein_ind}</div>
        <div>{cal_ind}</div>
      </div>
    </div>

    <!-- Coaching Brief -->
    <div style="background:{COLORS['card']};border-radius:12px;padding:24px;margin-bottom:16px;font-size:15px;line-height:1.7;">
      {brief_html}
    </div>

    <!-- Race Countdowns -->
    <div style="background:{COLORS['card']};border-radius:12px;padding:16px;text-align:center;font-size:13px;color:{COLORS['muted']};">
      <span style="margin:0 16px;color:{COLORS['accent']}">🏟️ Spartan: <strong style="color:{COLORS['text']}">{days_to_spartan}d</strong></span>
      <span style="margin:0 16px;color:{COLORS['accent']}">🏊 Triathlon: <strong style="color:{COLORS['text']}">{days_to_triathlon}d</strong></span>
      <span style="margin:0 16px;color:{COLORS['accent']}">⚡ Hyrox: <strong style="color:{COLORS['text']}">ongoing</strong></span>
    </div>

    <p style="text-align:center;font-size:11px;color:{COLORS['muted']};margin-top:12px;">
      Powered by Claude · Daily Coach
    </p>
  </div>
</body>
</html>"""


def _build_plain_text(coaching_brief_text: str, date_str: str, metrics_summary: dict) -> str:
    def fmt(key, unit="", decimals=0):
        v = metrics_summary.get(key)
        if v is None:
            return "N/A"
        return f"{v:.{decimals}f}{unit}" if decimals else f"{int(v)}{unit}"

    days_to_spartan = _days_until(SPARTAN_DATE)
    days_to_triathlon = _days_until(TRIATHLON_DATE)

    return f"""DAILY COACHING BRIEF — {date_str}
{'=' * 50}

YESTERDAY: Weight {fmt('weight_lbs', ' lbs', 1)} | Steps {fmt('steps')} | Sleep {fmt('sleep_hours', ' hrs', 1)} | Protein {fmt('protein_g', 'g')} | Active Cal {fmt('active_calories', ' kcal')}

{coaching_brief_text}

---
Spartan: {days_to_spartan}d | Triathlon: {days_to_triathlon}d | Hyrox: ongoing
"""


def send_coaching_email(
    coaching_brief_text: str,
    date_str: str,
    metrics_summary: dict,
):
    days_to_spartan = _days_until(SPARTAN_DATE)
    subject = f"🏋️ Daily Coaching Brief — {date_str} | {days_to_spartan}d to Spartan"

    html = _build_html(coaching_brief_text, date_str, metrics_summary)
    plain = _build_plain_text(coaching_brief_text, date_str, metrics_summary)

    message = Mail(
        from_email=os.environ["FROM_EMAIL"],
        to_emails=os.environ["TO_EMAIL"],
        subject=subject,
        html_content=html,
        plain_text_content=plain,
    )

    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    response = sg.send(message)
    print(f"[SendGrid] Email sent — status: {response.status_code}")
    return response
