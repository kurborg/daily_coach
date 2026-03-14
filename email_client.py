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
    # Discipline & consistency
    ("Pain is temporary. Quitting lasts forever.", "Lance Armstrong"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
    ("Obsessed is a word the lazy use to describe the dedicated.", "Unknown"),
    ("The only bad workout is the one that didn't happen.", "Unknown"),
    ("Wake up with determination. Go to bed with satisfaction.", "Unknown"),
    ("Don't wish it were easier. Wish you were better.", "Jim Rohn"),
    ("Success is the sum of small efforts, repeated day in and day out.", "Robert Collier"),
    ("Motivation gets you started. Habit keeps you going.", "Jim Ryun"),
    ("The man who masters himself is free.", "Epictetus"),
    ("Discipline equals freedom.", "Jocko Willink"),
    ("Small daily improvements over time lead to stunning results.", "Robin Sharma"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("You'll never always be motivated, so you must learn to be disciplined.", "Unknown"),
    ("It's not about perfect. It's about effort.", "Jillian Michaels"),
    # Physique & body composition
    ("The body achieves what the mind believes.", "Napoleon Hill"),
    ("Take care of your body. It's the only place you have to live.", "Jim Rohn"),
    ("To keep the body in good health is a duty — otherwise we shall not be able to keep our mind strong and clear.", "Buddha"),
    ("Your body is your most priceless possession. Take care of it.", "Jack LaLanne"),
    ("Muscles are torn in the gym, fed in the kitchen, and built in bed.", "Unknown"),
    ("The groundwork for all happiness is good health.", "Leigh Hunt"),
    ("A fit body, a calm mind, a house full of love. These things cannot be bought — they must be earned.", "Naval Ravikant"),
    ("Looking good is a consequence of doing the work.", "Unknown"),
    ("Sweat is just fat crying.", "Unknown"),
    ("Train insane or remain the same.", "Jillian Michaels"),
    # Strength & mental toughness
    ("If it doesn't challenge you, it doesn't change you.", "Fred DeVito"),
    ("Champions aren't made in gyms. They are made from something deep inside.", "Muhammad Ali"),
    ("Hard work beats talent when talent doesn't work hard.", "Tim Notke"),
    ("It never gets easier. You just get better.", "Unknown"),
    ("The only way to define your limits is by going beyond them.", "Arthur C. Clarke"),
    ("Your body can stand almost anything. It's your mind you have to convince.", "Unknown"),
    ("Strength does not come from physical capacity. It comes from indomitable will.", "Mahatma Gandhi"),
    ("You didn't come this far to only come this far.", "Unknown"),
    ("Fall seven times, stand up eight.", "Japanese Proverb"),
    ("Every champion was once a contender who refused to give up.", "Rocky Balboa"),
    ("Do not pray for an easy life; pray for the strength to endure a difficult one.", "Bruce Lee"),
    ("The pain you feel today is the strength you'll feel tomorrow.", "Unknown"),
    ("What hurts today makes you stronger tomorrow.", "Jay Cutler"),
    ("Strength is not given. It is built.", "Unknown"),
    ("Push yourself because no one else is going to do it for you.", "Unknown"),
    ("Courage is not the absence of fear, but taking action in spite of it.", "Mark Twain"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    # Identity & mindset
    ("Be who you needed when you were younger.", "Unknown"),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("Do something today that your future self will thank you for.", "Sean Patrick Flanery"),
    ("Don't count the days. Make the days count.", "Muhammad Ali"),
    ("The difference between who you are and who you want to be is what you do.", "Unknown"),
    ("Don't be afraid to give up the good to go for the great.", "John D. Rockefeller"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("Act the way you want to feel.", "Gretchen Rubin"),
    ("Identity is the biggest lever. Once you decide who you are, the behaviors follow.", "James Clear"),
    ("Every action you take is a vote for the person you wish to become.", "James Clear"),
    ("You are confined only by the walls you build yourself.", "Andrew Murphy"),
    # Stoic / philosophical
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("Waste no more time arguing what a good man should be. Be one.", "Marcus Aurelius"),
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("He who is brave is free.", "Seneca"),
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("The greatest wealth is to live content with little.", "Plato"),
    # Nutrition & recovery
    ("Let food be thy medicine and medicine be thy food.", "Hippocrates"),
    ("You can't out-train a bad diet.", "Unknown"),
    ("Rest when you're weary. Refresh and renew yourself, your body, your mind, your spirit.", "Ralph Marston"),
    ("Recovery is where the growth actually happens.", "Unknown"),
    ("Sleep is the greatest legal performance-enhancing drug.", "Matthew Walker"),
    # Grit & perseverance
    ("It's supposed to be hard. If it were easy, everyone would do it.", "Tom Hanks"),
    ("The harder the battle, the sweeter the victory.", "Les Brown"),
    ("A river cuts through rock not because of its power, but its persistence.", "James N. Watkins"),
    ("Grit is living life like it's a marathon, not a sprint.", "Angela Duckworth"),
    ("Fall in love with the process and the results will come.", "Unknown"),
    ("The grind doesn't stop because you're tired. The grind stops when you're done.", "Unknown"),
    ("Success isn't owned. It's leased, and rent is due every day.", "J.J. Watt"),
    ("You were not built to be comfortable.", "Unknown"),
    ("There are no shortcuts to any place worth going.", "Beverly Sills"),
    ("Great things never came from comfort zones.", "Neil Strauss"),
    # Performance & competition
    ("The only competition you have is who you were yesterday.", "Unknown"),
    ("Don't run from the challenge. Run toward the goal.", "Unknown"),
    ("Champions do not become champions when they win events, but in the hours, weeks, months, and years they spend preparing for it.", "T. Alan Armstrong"),
    ("Gold medals aren't really made of gold. They're made of sweat, determination, and a hard-to-find alloy called guts.", "Dan Gable"),
    ("You can't put a limit on anything. The more you dream, the farther you get.", "Michael Phelps"),
    ("Do not go where the path may lead; go instead where there is no path and leave a trail.", "Ralph Waldo Emerson"),
    ("Hard work beats talent when talent fails to work hard.", "Kevin Durant"),
    ("The key is not the will to win. Everybody has that. It is the will to prepare to win.", "Bobby Knight"),
    ("I hated every minute of training, but I said: don't quit. Suffer now and live the rest of your life as a champion.", "Muhammad Ali"),
    ("Winning means you're willing to go longer, work harder, and give more than anyone else.", "Vince Lombardi"),
    ("You have to expect things of yourself before you can do them.", "Michael Jordan"),
    ("I've missed more than 9,000 shots. I've failed over and over and over again in my life. And that is why I succeed.", "Michael Jordan"),
    ("There may be people that have more talent than you, but there's no excuse for anyone to work harder than you do.", "Derek Jeter"),
]

BIBLE_VERSES = [
    # Strength & courage
    ("I can do all things through Christ who strengthens me.", "Philippians 4:13"),
    ("Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go.", "Joshua 1:9"),
    ("The Lord is my strength and my shield; my heart trusts in him, and he helps me.", "Psalm 28:7"),
    ("Be strong in the Lord and in his mighty power.", "Ephesians 6:10"),
    ("The Lord gives strength to the weary and increases the power of the weak.", "Isaiah 40:29"),
    ("For God has not given us a spirit of fear, but of power and of love and of a sound mind.", "2 Timothy 1:7"),
    ("God is our refuge and strength, an ever-present help in trouble.", "Psalm 46:1"),
    ("My flesh and my heart may fail, but God is the strength of my heart and my portion forever.", "Psalm 73:26"),
    ("I lift up my eyes to the mountains — where does my help come from? My help comes from the Lord.", "Psalm 121:1-2"),
    ("He gives power to the faint, and to him who has no might he increases strength.", "Isaiah 40:29"),
    ("In all these things we are more than conquerors through him who loved us.", "Romans 8:37"),
    ("The name of the Lord is a strong tower; the righteous man runs into it and is safe.", "Proverbs 18:10"),
    # Perseverance & discipline
    ("No discipline seems pleasant at the time, but painful. Later on, however, it produces a harvest of righteousness and peace.", "Hebrews 12:11"),
    ("Therefore, since we are surrounded by such a great cloud of witnesses, let us throw off everything that hinders... and run with perseverance the race marked out for us.", "Hebrews 12:1"),
    ("I have fought the good fight, I have finished the race, I have kept the faith.", "2 Timothy 4:7"),
    ("Blessed is the one who perseveres under trial because, having stood the test, they will receive the crown of life.", "James 1:12"),
    ("Not that I have already obtained all this, or have already arrived at my goal, but I press on.", "Philippians 3:12"),
    ("Let us not become weary in doing good, for at the proper time we will reap a harvest if we do not give up.", "Galatians 6:9"),
    ("Consider it pure joy, my brothers, whenever you face trials of many kinds, because the testing of your faith develops perseverance.", "James 1:2-3"),
    ("Run in such a way as to get the prize. Everyone who competes goes into strict training.", "1 Corinthians 9:24-25"),
    ("I press on toward the goal to win the prize for which God has called me heavenward in Christ Jesus.", "Philippians 3:14"),
    ("And let us run with endurance the race that is set before us.", "Hebrews 12:1"),
    # Faith & trust
    ("Trust in the Lord with all your heart and lean not on your own understanding.", "Proverbs 3:5"),
    ("For we walk by faith, not by sight.", "2 Corinthians 5:7"),
    ("For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you.", "Jeremiah 29:11"),
    ("And we know that in all things God works for the good of those who love him.", "Romans 8:28"),
    ("Commit to the Lord whatever you do, and he will establish your plans.", "Proverbs 16:3"),
    ("The Lord will fight for you; you need only to be still.", "Exodus 14:14"),
    ("Cast all your anxiety on him because he cares for you.", "1 Peter 5:7"),
    ("Delight yourself in the Lord, and he will give you the desires of your heart.", "Psalm 37:4"),
    ("And my God will meet all your needs according to the riches of his glory in Christ Jesus.", "Philippians 4:19"),
    ("For nothing will be impossible with God.", "Luke 1:37"),
    ("If God is for us, who can be against us?", "Romans 8:31"),
    # Hope & renewal
    ("But those who hope in the Lord will renew their strength. They will soar on wings like eagles.", "Isaiah 40:31"),
    ("Create in me a clean heart, O God, and renew a steadfast spirit within me.", "Psalm 51:10"),
    ("He restores my soul.", "Psalm 23:3"),
    ("The Lord's mercies are new every morning; great is your faithfulness.", "Lamentations 3:22-23"),
    ("He gives strength to the weary and increases the power of the weak.", "Isaiah 40:29"),
    ("Come to me, all you who are weary and burdened, and I will give you rest.", "Matthew 11:28"),
    ("Do not be anxious about anything, but in every situation, by prayer and petition, present your requests to God.", "Philippians 4:6"),
    ("And the peace of God, which transcends all understanding, will guard your hearts and your minds.", "Philippians 4:7"),
    ("May the God of hope fill you with all joy and peace as you trust in him.", "Romans 15:13"),
    ("He will wipe every tear from their eyes. There will be no more death or mourning or crying or pain.", "Revelation 21:4"),
    # Purpose & diligence
    ("So whether you eat or drink or whatever you do, do it all for the glory of God.", "1 Corinthians 10:31"),
    ("Whatever you do, work at it with all your heart, as working for the Lord, not for human masters.", "Colossians 3:23"),
    ("For we are God's handiwork, created in Christ Jesus to do good works.", "Ephesians 2:10"),
    ("Do you not know that your bodies are temples of the Holy Spirit?", "1 Corinthians 6:19"),
    ("The plans of the diligent lead to profit as surely as haste leads to poverty.", "Proverbs 21:5"),
    ("Diligent hands will rule, but laziness ends in forced labor.", "Proverbs 12:24"),
    ("She sets about her work vigorously; her arms are strong for her tasks.", "Proverbs 31:17"),
    ("A sluggard's appetite is never filled, but the desires of the diligent are fully satisfied.", "Proverbs 13:4"),
    ("Do not be overcome by evil, but overcome evil with good.", "Romans 12:21"),
    ("Whatever your hand finds to do, do it with all your might.", "Ecclesiastes 9:10"),
    # Identity & transformation
    ("Therefore, if anyone is in Christ, the new creation has come: The old has gone, the new is here!", "2 Corinthians 5:17"),
    ("Do not conform to the pattern of this world, but be transformed by the renewing of your mind.", "Romans 12:2"),
    ("For we are his workmanship, created in Christ Jesus for good works.", "Ephesians 2:10"),
    ("I praise you because I am fearfully and wonderfully made.", "Psalm 139:14"),
    ("Before I formed you in the womb I knew you; before you were born I set you apart.", "Jeremiah 1:5"),
    ("See what great love the Father has lavished on us, that we should be called children of God!", "1 John 3:1"),
    ("You are the light of the world. A town built on a hill cannot be hidden.", "Matthew 5:14"),
    # Guidance & wisdom
    ("Even though I walk through the darkest valley, I will fear no evil, for you are with me.", "Psalm 23:4"),
    ("Your word is a lamp for my feet, a light on my path.", "Psalm 119:105"),
    ("For the Spirit God gave us does not make us timid, but gives us power, love and self-discipline.", "2 Timothy 1:7"),
    ("Where there is no vision, the people perish.", "Proverbs 29:18"),
    ("Do not despise these small beginnings, for the Lord rejoices to see the work begin.", "Zechariah 4:10"),
    ("Ask and it will be given to you; seek and you will find; knock and the door will be opened to you.", "Matthew 7:7"),
    ("The heart of man plans his way, but the Lord establishes his steps.", "Proverbs 16:9"),
    ("In their hearts humans plan their course, but the Lord establishes their steps.", "Proverbs 16:9"),
    ("Teach us to number our days, that we may gain a heart of wisdom.", "Psalm 90:12"),
    ("The beginning of wisdom is this: Get wisdom, and whatever you get, get insight.", "Proverbs 4:7"),
    # Gratitude & contentment
    ("Give thanks to the Lord, for he is good; his love endures forever.", "Psalm 107:1"),
    ("I have learned, in whatever state I am, to be content.", "Philippians 4:11"),
    ("This is the day the Lord has made; let us rejoice and be glad in it.", "Psalm 118:24"),
    ("Every good and perfect gift is from above.", "James 1:17"),
    ("Rejoice always, pray continually, give thanks in all circumstances.", "1 Thessalonians 5:16-18"),
    ("The Lord bless you and keep you; the Lord make his face shine on you.", "Numbers 6:24-25"),
]


def _days_until(target: date) -> int:
    return max(0, (target - date.today()).days)


def _daily_pick(items: list) -> tuple:
    """Pick deterministically by date so it's consistent all day."""
    seed = int(date.today().strftime("%Y%m%d"))
    rng = random.Random(seed + id(items))
    return rng.choice(items)


def _metric_card(emoji: str, label: str, value, unit: str, target,
                 higher_is_better: bool = True, decimals: int = 0) -> str:
    if value is None:
        pct = 0
        pct_label = "Not logged"
        display = "N/A"
        status_color = MUTED
        status_icon = "—"
        bar_color = MUTED
        note = "Not logged"
    elif target is None:
        # Informational — no goal set, just show the value neutrally
        display = f"{value:.{decimals}f}" if decimals else f"{int(value)}"
        pct = 0
        pct_label = "No goal set"
        status_color = MUTED
        status_icon = "📍"
        bar_color = MUTED
        note = "Logged"
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
        pct_label = f"{pct}% of goal"
        note = f"Goal: {int(target)}{unit}" if decimals == 0 else f"Goal: {target:.{decimals}f}{unit}"

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
            <div style="font-size:10px;color:{MUTED};margin-top:5px;">{pct_label}</div>
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


def _resolve_target(cfg: dict, card: dict, metrics_summary: dict):
    """Resolve card target. Returns None if no target_ref is set (informational card)."""
    if not card.get("target_ref"):
        return None
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
        goal_str = f"  (goal: {target})" if target is not None else ""
        metric_lines.append(f"    {card['emoji']}  {card['label']}: {val_str}{goal_str}")
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


def _build_workout_rows(metrics_summary: dict) -> str:
    workouts = metrics_summary.get("workouts", [])
    derived  = metrics_summary.get("derived_activities", [])
    activities = workouts if workouts else derived

    if not activities:
        return f'<p style="font-size:14px;color:{MUTED};margin:0;padding:4px 0;">No workouts logged today.</p>'

    rows = []
    for a in activities:
        if "duration_min" in a:
            parts = [f'{a["duration_min"]:.0f} min']
            if a.get("distance_mi"):
                parts.append(f'{a["distance_mi"]:.2f} mi')
            if a.get("active_energy"):
                parts.append(f'{int(a["active_energy"])} kcal')
            if a.get("avg_hr"):
                parts.append(f'avg HR {int(a["avg_hr"])} bpm')
            details = " · ".join(parts)
        else:
            details = f'{a["distance_mi"]:.2f} mi'

        rows.append(
            f'<tr><td style="padding:12px 16px;border-bottom:1px solid {BORDER};">'
            f'<div style="font-size:14px;font-weight:600;color:{TEXT};">🏋️ {a["name"]}</div>'
            f'<div style="font-size:12px;color:{MUTED};margin-top:3px;">{details}</div>'
            f'</td></tr>'
        )
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        + "".join(rows)
        + "</table>"
    )


def _build_nutrition_bars(metrics_summary: dict, cfg: dict) -> str:
    t = cfg.get("daily_targets", {})
    items = [
        ("Calories", metrics_summary.get("calories_consumed"), t.get("calories_rest_day"), " kcal", ACCENT),
        ("Protein",  metrics_summary.get("protein_g"),         t.get("protein_g"),         "g",     GREEN),
        ("Carbs",    metrics_summary.get("carbs_g"),           None,                        "g",     GOLD),
        ("Fat",      metrics_summary.get("fat_g"),             t.get("fat_g_min"),          "g",     ORANGE),
    ]
    rows = []
    for label, val, target, unit, color in items:
        if val is None:
            rows.append(
                f'<tr><td style="padding:5px 0;">'
                f'<span style="font-size:12px;color:{MUTED};">{label}: Not logged</span>'
                f'</td></tr>'
            )
            continue
        pct = min(100, int((val / target) * 100)) if target else 50
        on = (val >= target) if target else True
        bar_c = GREEN if on else (ORANGE if pct >= 75 else RED)
        rows.append(
            f'<tr><td style="padding:6px 0;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td width="70"><span style="font-size:12px;color:{MUTED};">{label}</span></td>'
            f'<td><div style="background:{BORDER};border-radius:3px;height:6px;">'
            f'<div style="width:{pct}%;height:6px;background:{bar_c};border-radius:3px;"></div>'
            f'</div></td>'
            f'<td width="80" align="right"><span style="font-size:12px;font-weight:600;color:{TEXT};">'
            f'{int(val)}{unit}</span></td>'
            f'</tr></table>'
            f'</td></tr>'
        )
    return f'<table width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(rows)}</table>'


def _build_review_html(date_str: str, metrics_summary: dict, cfg: dict) -> str:
    name   = cfg["profile"]["name"]
    events = cfg.get("events", [])

    quote_text, quote_author = _daily_pick(MOTIVATIONAL_QUOTES)
    verse_text, verse_ref   = _daily_pick(BIBLE_VERSES)

    # Event countdowns header (optional)
    first_event = next((e for e in events if e["date"]), None)
    if first_event:
        d = datetime.strptime(first_event["date"], "%Y-%m-%d").date()
        header_countdown = (
            f'<div style="text-align:right;">'
            f'<div style="font-size:11px;color:{MUTED};letter-spacing:1px;margin-bottom:4px;">{first_event["short"].upper()}</div>'
            f'<div style="font-size:24px;font-weight:800;color:{ACCENT};">{_days_until(d)}</div>'
            f'<div style="font-size:10px;color:{MUTED};">days away</div>'
            f'</div>'
        )
    else:
        header_countdown = ""

    metric_grid     = _build_metric_grid(cfg, metrics_summary)
    workout_rows    = _build_workout_rows(metrics_summary)
    nutrition_bars  = _build_nutrition_bars(metrics_summary, cfg)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Day in Review</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BG};">
  <tr><td align="center" style="padding:24px 12px;">
  <table width="620" cellpadding="0" cellspacing="0" border="0" style="max-width:620px;width:100%;">

    <!-- ═══ HEADER ═══ -->
    <tr>
      <td style="background:linear-gradient(135deg,#0d1b3e 0%,#1a1a2e 50%,#0d2a3e 100%);
                 border-radius:16px;padding:28px 30px 24px;border-bottom:3px solid {GOLD};">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td>
              <div style="font-size:11px;color:{MUTED};letter-spacing:3px;text-transform:uppercase;margin-bottom:6px;">
                Day in Review
              </div>
              <div style="font-size:28px;font-weight:800;color:{WHITE};line-height:1.2;">
                🌙 {name}'s Day
              </div>
              <div style="font-size:13px;color:{MUTED};margin-top:6px;">{date_str}</div>
            </td>
            <td align="right" style="vertical-align:top;">{header_countdown}</td>
          </tr>
        </table>
      </td>
    </tr>

    <tr><td style="height:14px;"></td></tr>

    <!-- ═══ METRICS GRID ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:20px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:14px;">
          📊 &nbsp;Today's Numbers
        </div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
{metric_grid}
        </table>
      </td>
    </tr>

    <tr><td style="height:10px;"></td></tr>

    <!-- ═══ WORKOUTS ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:20px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:14px;">
          🏋️ &nbsp;Workouts
        </div>
        {workout_rows}
      </td>
    </tr>

    <tr><td style="height:10px;"></td></tr>

    <!-- ═══ NUTRITION ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:20px;">
        <div style="font-size:11px;color:{MUTED};letter-spacing:2px;
                    text-transform:uppercase;font-weight:700;margin-bottom:14px;">
          🥗 &nbsp;Nutrition
        </div>
        {nutrition_bars}
      </td>
    </tr>

    <tr><td style="height:10px;"></td></tr>

    <!-- ═══ BIBLE VERSE ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:18px 24px;border-left:4px solid {GOLD};">
        <div style="font-size:11px;color:{GOLD};letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:8px;">
          ✝️ &nbsp;Verse of the Day
        </div>
        <div style="font-size:14px;color:{TEXT};line-height:1.7;font-style:italic;">"{verse_text}"</div>
        <div style="font-size:12px;color:{GOLD};margin-top:8px;font-weight:600;">— {verse_ref}</div>
      </td>
    </tr>

    <tr><td style="height:10px;"></td></tr>

    <!-- ═══ QUOTE ═══ -->
    <tr>
      <td style="background:{CARD};border-radius:14px;padding:18px 24px;border-left:4px solid {ACCENT};">
        <div style="font-size:11px;color:{ACCENT};letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:8px;">
          🔥 &nbsp;End Strong
        </div>
        <div style="font-size:14px;color:{TEXT};line-height:1.7;font-style:italic;">"{quote_text}"</div>
        <div style="font-size:12px;color:{ACCENT};margin-top:6px;font-weight:600;">— {quote_author}</div>
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


def _build_review_plain(date_str: str, metrics_summary: dict, cfg: dict) -> str:
    name = cfg["profile"]["name"]
    m    = metrics_summary

    quote_text, quote_author = _daily_pick(MOTIVATIONAL_QUOTES)
    verse_text, verse_ref   = _daily_pick(BIBLE_VERSES)

    metric_lines = []
    for card in cfg.get("metric_cards", []):
        v       = m.get(card["data_key"])
        target  = _resolve_target(cfg, card, m)
        d       = card.get("decimals", 0)
        val_str = "N/A" if v is None else (f"{v:.{d}f}{card.get('unit','')}" if d else f"{int(v)}{card.get('unit','')}")
        goal    = f"  (goal: {target})" if target is not None else ""
        metric_lines.append(f"    {card['emoji']}  {card['label']}: {val_str}{goal}")

    workouts = m.get("workouts", []) or m.get("derived_activities", [])
    workout_lines = []
    for a in workouts:
        if "duration_min" in a:
            line = f'    - {a["name"]}: {a["duration_min"]:.0f} min'
            if a.get("distance_mi"): line += f', {a["distance_mi"]:.2f} mi'
            if a.get("active_energy"): line += f', {int(a["active_energy"])} kcal'
        else:
            line = f'    - {a["name"]}: {a["distance_mi"]:.2f} mi'
        workout_lines.append(line)
    workouts_str = "\n".join(workout_lines) if workout_lines else "    No workouts logged."

    def fmt(v, unit="", d=0):
        return "N/A" if v is None else (f"{v:.{d}f}{unit}" if d else f"{int(v)}{unit}")

    return f"""{name.upper()}'S DAY IN REVIEW — {date_str}
{'=' * 56}

✝️  "{verse_text}"
    — {verse_ref}

🔥  "{quote_text}"
    — {quote_author}

{'=' * 56}
📊  TODAY'S NUMBERS
{chr(10).join(metric_lines)}

{'=' * 56}
🏋️  WORKOUTS
{workouts_str}

{'=' * 56}
🥗  NUTRITION
    Calories: {fmt(m.get('calories_consumed'), ' kcal')}
    Protein:  {fmt(m.get('protein_g'), 'g')}
    Carbs:    {fmt(m.get('carbs_g'), 'g')}
    Fat:      {fmt(m.get('fat_g'), 'g')}

{'=' * 56}
Powered by Claude · Built for {name}
"""


def send_review_email(
    date_str: str,
    metrics_summary: dict,
    to_email: str,
    cfg: dict,
):
    name = cfg["profile"]["name"]
    subject = f"🌙 {name}'s Day in Review — {date_str}"

    html  = _build_review_html(date_str, metrics_summary, cfg)
    plain = _build_review_plain(date_str, metrics_summary, cfg)

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

    print(f"[Gmail] Review email sent to {to_email}")


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

    subject = f"{name}'s Fitness Brief — {date_str}{countdown_str}"

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
