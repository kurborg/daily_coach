import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime
from config_loader import resolve_ref

# ── Color Palette ─────────────────────────────────────────────────────────────
BG      = "#0d0d1a"
CARD    = "#151528"
CARD2   = "#1c1c35"
ACCENT  = "#00c8ff"
GOLD    = "#f5c842"
TEXT    = "#e8e8f4"
MUTED   = "#6e6e9a"
GREEN   = "#00d68f"
RED     = "#ff5c5c"
ORANGE  = "#ffaa00"
BORDER  = "#252545"
WHITE   = "#ffffff"

# ── Quotes & Verses ───────────────────────────────────────────────────────────
MOTIVATIONAL_QUOTES = [
    ("Pain is temporary. Quitting lasts forever.", "Lance Armstrong"),
    ("The only way to define your limits is by going beyond them.", "Arthur C. Clarke"),
    ("If it doesn't challenge you, it doesn't change you.", "Fred DeVito"),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("The body achieves what the mind believes.", "Napoleon Hill"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("Champions aren't made in gyms. They are made from something deep inside.", "Muhammad Ali"),
    ("No pain, no gain. Shut up and train.", "Unknown"),
    ("The difference between try and triumph is just a little umph.", "Marvin Phillips"),
    ("Success is the sum of small efforts, repeated day in and day out.", "Robert Collier"),
    ("Your body can stand almost anything. It's your mind you have to convince.", "Unknown"),
    ("Hard work beats talent when talent doesn't work hard.", "Tim Notke"),
    ("It never gets easier. You just get better.", "Unknown"),
    ("Do something today that your future self will thank you for.", "Sean Patrick Flanery"),
    ("Train insane or remain the same.", "Jillian Michaels"),
    ("Obsessed is a word the lazy use to describe the dedicated.", "Unknown"),
    ("The only bad workout is the one that didn't happen.", "Unknown"),
    ("You didn't come this far to only come this far.", "Unknown"),
    ("Fall seven times, stand up eight.", "Japanese Proverb"),
    ("The groundwork for all happiness is good health.", "Leigh Hunt"),
    ("Strength does not come from physical capacity. It comes from indomitable will.", "Mahatma Gandhi"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Don't wish it were easier. Wish you were better.", "Jim Rohn"),
    ("Be patient with yourself. Self-growth is tender; it's holy ground.", "Stephen Covey"),
    ("What hurts today makes you stronger tomorrow.", "Jay Cutler"),
    ("Push yourself because no one else is going to do it for you.", "Unknown"),
    ("Wake up with determination. Go to bed with satisfaction.", "Unknown"),
    ("The pain you feel today is the strength you'll feel tomorrow.", "Unknown"),
    ("Courage is not the absence of fear, but taking action in spite of it.", "Mark Twain"),
    ("Every champion was once a contender who refused to give up.", "Rocky Balboa"),
]

BIBLE_VERSES = [
    ("I can do all things through Christ who strengthens me.", "Philippians 4:13"),
    ("Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go.", "Joshua 1:9"),
    ("But those who hope in the Lord will renew their strength. They will soar on wings like eagles; they will run and not grow weary, they will walk and not be faint.", "Isaiah 40:31"),
    ("Do you not know that in a race all the runners run, but only one gets the prize? Run in such a way as to get the prize.", "1 Corinthians 9:24"),
    ("For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.", "Jeremiah 29:11"),
    ("The Lord is my strength and my shield; my heart trusts in him, and he helps me.", "Psalm 28:7"),
    ("No discipline seems pleasant at the time, but painful. Later on, however, it produces a harvest of righteousness and peace.", "Hebrews 12:11"),
    ("So whether you eat or drink or whatever you do, do it all for the glory of God.", "1 Corinthians 10:31"),
    ("Have I not commanded you? Be strong and courageous!", "Joshua 1:9"),
    ("Therefore, since we are surrounded by such a great cloud of witnesses, let us throw off everything that hinders... and run with perseverance the race marked out for us.", "Hebrews 12:1"),
    ("God is our refuge and strength, an ever-present help in trouble.", "Psalm 46:1"),
    ("And we know that in all things God works for the good of those who love him.", "Romans 8:28"),
    ("Do not be anxious about anything, but in every situation, by prayer and petition... present your requests to God.", "Philippians 4:6"),
    ("The Lord will fight for you; you need only to be still.", "Exodus 14:14"),
    ("Create in me a clean heart, O God, and renew a steadfast spirit within me.", "Psalm 51:10"),
    ("Even though I walk through the darkest valley, I will fear no evil, for you are with me.", "Psalm 23:4"),
    ("Commit to the Lord whatever you do, and he will establish your plans.", "Proverbs 16:3"),
    ("Be strong in the Lord and in his mighty power.", "Ephesians 6:10"),
    ("Trust in the Lord with all your heart and lean not on your own understanding.", "Proverbs 3:5"),
    ("The Lord gives strength to the weary and increases the power of the weak.", "Isaiah 40:29"),
    ("I have fought the good fight, I have finished the race, I have kept the faith.", "2 Timothy 4:7"),
    ("For God has not given us a spirit of fear, but of power and of love and of a sound mind.", "2 Timothy 1:7"),
    ("Blessed is the one who perseveres under trial because, having stood the test, they will receive the crown of life.", "James 1:12"),
    ("For we walk by faith, not by sight.", "2 Corinthians 5:7"),
    ("Not that I have already obtained all this, or have already arrived at my goal, but I press on to take hold of that for which Christ Jesus took hold of me.", "Philippians 3:12"),
    ("He gives strength to the weary and increases the power of the weak.", "Isaiah 40:29"),
    ("My flesh and my heart may fail, but God is the strength of my heart and my portion forever.", "Psalm 73:26"),
    ("I lift up my eyes to the mountains — where does my help come from? My help comes from the Lord.", "Psalm 121:1-2"),
    ("Come to me, all you who are weary and burdened, and I will give you rest.", "Matthew 11:28"),
    ("Whatever you do, work at it with all your heart, as working for the Lord, not for human masters.", "Colossians 3:23"),
]


def _days_until(target: date) -> int:
    return max(0, (target - date.today()).days)


def _daily_pick(items: list) -> tuple:
    """Pick deterministically by date so it's consistent all day."""
    seed = int(date.today().strftime("%Y%m%d"))
    rng = random.Random(seed + id(items))
    return rng.choice(items)


def _metric_card(emoji: str, label: str, value, unit: str, target: float,
                 higher_is_better: bool = True, decimals: int = 0) -> str:
    if value is None:
        pct = 0
        display = "N/A"
        status_color = MUTED
        status_icon = "—"
        bar_color = MUTED
        note = "Not logged"
    else:
        display = f"{value:.{decimals}f}" if decimals else f"{int(value)}"
        on_target = (value >= target) if higher_is_better else (value <= target)
        status_color = GREEN if on_target else RED
        status_icon = "✅" if on_target else "❌"
        if higher_is_better:
            pct = min(100, int((value / target) * 100))
        else:
            pct = min(100, int((target / value) * 100)) if value > 0 else 100
        bar_color = GREEN if on_target else (ORANGE if pct >= 75 else RED)
        diff = value - target if higher_is_better else target - value
        note = f"Goal: {int(target)}{unit}" if decimals == 0 else f"Goal: {target:.1f}{unit}"

    return f"""
    <td width="48%" style="vertical-align:top;padding:6px 0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{CARD2};border-radius:12px;border:1px solid {BORDER};">
        <tr>
          <td style="padding:16px 16px 8px;">
            <div style="font-size:22px;margin-bottom:4px;">{emoji}</div>
            <div style="font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;font-weight:600;">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{TEXT};margin:4px 0 2px;">{display}<span style="font-size:14px;color:{MUTED};font-weight:400;">{unit}</span></div>
            <div style="font-size:11px;color:{status_color};">{status_icon} {note}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:0 16px 14px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="background:{BORDER};border-radius:4px;height:5px;">
                  <div style="width:{pct}%;height:5px;background:{bar_color};border-radius:4px;"></div>
                </td>
              </tr>
            </table>
            <div style="font-size:10px;color:{MUTED};margin-top:5px;">{pct}% of goal</div>
          </td>
        </tr>
      </table>
    </td>"""


def _section_header(emoji: str, title: str) -> str:
    return f"""
    <tr>
      <td style="padding:8px 0 6px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="border-bottom:2px solid {ACCENT};padding-bottom:8px;">
              <span style="font-size:18px;font-weight:700;color:{ACCENT};letter-spacing:1px;">
                {emoji} {title}
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _format_brief_html(coaching_brief_text: str) -> str:
    """Style the coaching brief — highlight section headers and format text."""
    lines = coaching_brief_text.split("\n")
    html_lines = []
    in_directives = False

    section_map = {
        "YESTERDAY'S REPORT": ("📊", "YESTERDAY'S REPORT"),
        "FLAGS":               ("🚩", "FLAGS"),
        "TODAY'S DIRECTIVES": ("🎯", "TODAY'S DIRECTIVES"),
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        matched = False
        for key, (emoji, label) in section_map.items():
            if key in line.upper():
                if key == "TODAY'S DIRECTIVES":
                    in_directives = True
                html_lines.append(
                    f'<div style="margin:20px 0 10px;padding-bottom:8px;border-bottom:1px solid {BORDER};">'
                    f'<span style="font-size:15px;font-weight:700;color:{ACCENT};letter-spacing:1px;">'
                    f'{emoji} {label}</span></div>'
                )
                matched = True
                break

        if not matched:
            if not line:
                html_lines.append('<div style="height:10px;"></div>')
            elif in_directives and line[:2] in ("1.", "2.", "3."):
                num = line[0]
                rest = line[2:].strip()
                colors = {"1": ACCENT, "2": GREEN, "3": GOLD}
                c = colors.get(num, ACCENT)
                html_lines.append(
                    f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0;">'
                    f'<tr>'
                    f'<td width="32" style="vertical-align:top;">'
                    f'<div style="width:26px;height:26px;background:{c};border-radius:50%;text-align:center;'
                    f'line-height:26px;font-size:13px;font-weight:700;color:{BG};">{num}</div>'
                    f'</td>'
                    f'<td style="vertical-align:top;padding-left:10px;padding-top:3px;">'
                    f'<span style="font-size:14px;color:{TEXT};line-height:1.6;">{rest}</span>'
                    f'</td></tr></table>'
                )
            else:
                html_lines.append(
                    f'<p style="margin:6px 0;font-size:14px;color:{TEXT};line-height:1.7;">{line}</p>'
                )
        i += 1

    return "\n".join(html_lines)


def _resolve_target(cfg: dict, card: dict, metrics_summary: dict) -> float:
    """Resolve card target, using training-day override if applicable."""
    if card.get("training_day_target_ref") and metrics_summary.get("workouts"):
        return resolve_ref(cfg, card["training_day_target_ref"])
    return resolve_ref(cfg, card["target_ref"])


def _render_card(card: dict, cfg: dict, metrics_summary: dict) -> str:
    """Render one metric card from config."""
    value = metrics_summary.get(card["data_key"])
    target = _resolve_target(cfg, card, metrics_summary)
    return _metric_card(
        card["emoji"], card["label"], value,
        card.get("unit", ""), target,
        card.get("higher_is_better", True),
        card.get("decimals", 0),
    )


def _build_metric_grid(cfg: dict, metrics_summary: dict) -> str:
    """Build the 2-column metric grid from cfg['metric_cards']."""
    cards = cfg.get("metric_cards", [])
    rows = []
    for i in range(0, len(cards), 2):
        left = _render_card(cards[i], cfg, metrics_summary)
        if i + 1 < len(cards):
            right = _render_card(cards[i + 1], cfg, metrics_summary)
        else:
            right = '<td width="48%"></td>'
        rows.append(f"""          <tr>
            {left}
            <td width="4%"></td>
            {right}
          </tr>
          <tr><td colspan="3" style="height:10px;"></td></tr>""")
    return "\n".join(rows)


def _build_html(coaching_brief_text: str, date_str: str, metrics_summary: dict, cfg: dict) -> str:
    events = cfg["events"]
    goals = cfg["goals"]
    name = cfg["profile"]["name"]

    quote_text, quote_author = _daily_pick(MOTIVATIONAL_QUOTES)
    verse_text, verse_ref = _daily_pick(BIBLE_VERSES)

    m = metrics_summary

    # Build race countdown cards from config
    event_cards = []
    card_colors = [ACCENT, GREEN, GOLD]
    col_pct = max(20, 96 // max(len(events), 1))
    for i, e in enumerate(events):
        color = card_colors[i % len(card_colors)]
        if e["date"]:
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            days = _days_until(d)
            count_html = f'<div style="font-size:28px;font-weight:800;color:{color};">{days}</div><div style="font-size:10px;color:{MUTED};margin-top:3px;">days</div>'
            date_html = f'<div style="font-size:10px;color:{MUTED};">{e["date"]}</div>'
        else:
            count_html = f'<div style="font-size:28px;font-weight:800;color:{color};">∞</div><div style="font-size:10px;color:{MUTED};margin-top:3px;">&nbsp;</div>'
            date_html = f'<div style="font-size:10px;color:{MUTED};">ongoing</div>'
        event_cards.append(
            f'<td width="{col_pct}%" align="center" '
            f'style="background:{CARD2};border-radius:10px;padding:14px 8px;border:1px solid {BORDER};">'
            f'{count_html}'
            f'<div style="font-size:12px;color:{TEXT};font-weight:600;margin-top:6px;">{e["emoji"]} {e["short"]}</div>'
            f'{date_html}'
            f'</td>'
        )
    # interleave spacer tds
    spacer = f'<td width="2%"></td>'
    event_row = spacer.join(event_cards)

    # First event for header countdown
    first_event = next((e for e in events if e["date"]), None)
    if first_event:
        first_d = datetime.strptime(first_event["date"], "%Y-%m-%d").date()
        header_countdown = f'''<div style="text-align:right;">
                <div style="font-size:11px;color:{MUTED};letter-spacing:1px;margin-bottom:4px;">{first_event["short"].upper()}</div>
                <div style="font-size:24px;font-weight:800;color:{ACCENT};">{_days_until(first_d)}</div>
                <div style="font-size:10px;color:{MUTED};">days away</div>
              </div>'''
    else:
        header_countdown = ""

    brief_html = _format_brief_html(coaching_brief_text)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Daily Coaching Brief</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BG};">
  <tr><td align="center" style="padding:24px 12px;">
  <table width="620" cellpadding="0" cellspacing="0" border="0" style="max-width:620px;width:100%;">

    <!-- ═══ HEADER ═══ -->
    <tr>
      <td style="background:linear-gradient(135deg,#0d1b3e 0%,#1a1a2e 50%,#0d2a3e 100%);
                 border-radius:16px;padding:28px 30px 24px;
                 border-bottom:3px solid {ACCENT};margin-bottom:0;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td>
              <div style="font-size:11px;color:{MUTED};letter-spacing:3px;text-transform:uppercase;margin-bottom:6px;">
                Daily Coaching Brief
              </div>
              <div style="font-size:28px;font-weight:800;color:{WHITE};line-height:1.2;">
                💪 {name}'s Brief
              </div>
              <div style="font-size:13px;color:{MUTED};margin-top:6px;">{date_str}</div>
            </td>
            <td align="right" style="vertical-align:top;">
              {header_countdown}
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ BIBLE VERSE ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:20px 24px;
                 border-left:4px solid {GOLD};">
        <div style="font-size:11px;color:{GOLD};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:8px;">
          ✝️ &nbsp;Verse of the Day
        </div>
        <div style="font-size:15px;color:{TEXT};line-height:1.7;font-style:italic;">
          "{verse_text}"
        </div>
        <div style="font-size:12px;color:{GOLD};margin-top:8px;font-weight:600;">
          — {verse_ref}
        </div>
      </td>
    </tr>

    <tr><td style="height:10px;"></td></tr>

    <!-- ═══ MOTIVATIONAL QUOTE ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:18px 24px;
                 border-left:4px solid {ACCENT};">
        <div style="font-size:11px;color:{ACCENT};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:8px;">
          🔥 &nbsp;Today's Fuel
        </div>
        <div style="font-size:14px;color:{TEXT};line-height:1.7;font-style:italic;">
          "{quote_text}"
        </div>
        <div style="font-size:12px;color:{ACCENT};margin-top:6px;font-weight:600;">
          — {quote_author}
        </div>
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ RACE COUNTDOWNS ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:18px 20px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:14px;">
          🏁 &nbsp;Race Countdowns
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>{event_row}</tr>
        </table>
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ KEY METRICS GRID ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:20px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:14px;">
          📊 &nbsp;Yesterday's Numbers
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
{_build_metric_grid(cfg, m)}
        </table>
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ COACHING BRIEF ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:24px 26px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:16px;">
          🤖 &nbsp;AI Coach Analysis
        </div>
        {brief_html}
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ FOOTER ═══ -->
    <tr>
      <td align="center" style="padding:16px 0 8px;">
        <div style="font-size:11px;color:{MUTED};line-height:1.8;">
          Powered by Claude · Built for {name}<br>
          <span style="color:{BORDER};">——————————————</span><br>
          <span style="font-size:10px;">Data from Apple Health via Health Auto Export</span>
        </div>
      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body>
</html>"""


def _build_plain_text(coaching_brief_text: str, date_str: str, metrics_summary: dict, cfg: dict) -> str:
    events = cfg["events"]
    name = cfg["profile"]["name"]

    quote_text, quote_author = _daily_pick(MOTIVATIONAL_QUOTES)
    verse_text, verse_ref = _daily_pick(BIBLE_VERSES)

    event_lines = []
    for e in events:
        if e["date"]:
            d = datetime.strptime(e["date"], "%Y-%m-%d").date()
            event_lines.append(f"    {e['emoji']}  {e['short']}: {_days_until(d)}d ({e['date']})")
        else:
            event_lines.append(f"    {e['emoji']}  {e['short']}: ongoing")
    events_str = "\n".join(event_lines)

    metric_lines = []
    for card in cfg.get("metric_cards", []):
        v = metrics_summary.get(card["data_key"])
        target = _resolve_target(cfg, card, metrics_summary)
        decimals = card.get("decimals", 0)
        if v is None:
            val_str = "N/A"
        elif decimals:
            val_str = f"{v:.{decimals}f}{card.get('unit','')}"
        else:
            val_str = f"{int(v)}{card.get('unit','')}"
        metric_lines.append(f"    {card['emoji']}  {card['label']}: {val_str}  (goal: {target})")
    metrics_block = "\n".join(metric_lines)

    return f"""{name.upper()}'S DAILY COACHING BRIEF — {date_str}
{'=' * 56}

✝️  "{verse_text}"
    — {verse_ref}

🔥  "{quote_text}"
    — {quote_author}

{'=' * 56}
🏁  RACE COUNTDOWNS
{events_str}

{'=' * 56}
📊  YESTERDAY'S NUMBERS
{metrics_block}

{'=' * 56}
{coaching_brief_text}

{'=' * 56}
Powered by Claude · Built for {name}
"""


def send_coaching_email(
    coaching_brief_text: str,
    date_str: str,
    metrics_summary: dict,
    to_email: str,
    cfg: dict,
):
    events = cfg["events"]
    name = cfg["profile"]["name"]

    first_event = next((e for e in events if e["date"]), None)
    if first_event:
        d = datetime.strptime(first_event["date"], "%Y-%m-%d").date()
        countdown_str = f" | {_days_until(d)}d to {first_event['short']}"
    else:
        countdown_str = ""

    subject = f"💪 {name}'s Brief — {date_str}{countdown_str}"

    html  = _build_html(coaching_brief_text, date_str, metrics_summary, cfg)
    plain = _build_plain_text(coaching_brief_text, date_str, metrics_summary, cfg)

    from_email = os.environ["FROM_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, os.environ["GMAIL_APP_PASSWORD"])
        server.sendmail(from_email, to_email, msg.as_string())

    print(f"[Gmail] Email sent to {to_email}")
