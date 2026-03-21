# Getting Started with Daily Coach

Your AI coaching system pulls data from your Apple Health automatically and emails you a personalized daily coaching brief. Setup takes about 15 minutes.

---

## How it works (overview)

```
iPhone (Apple Health)
       │
       ▼ Health Auto Export app
Google Drive folder  ──────────────────────────────────────────┐
(your health data)                                             │
                                                               ▼
                                        daily-coach-configs/ (central folder)
                                        └── yourname.json  ◄── you upload this
                                                               │
                                                               ▼
                                                    Backend (GitHub Actions)
                                                    reads your config + fetches
                                                    your health data → Claude AI
                                                    → coaching email → you
```

**Two things you're responsible for:**
1. Exporting your health data to Google Drive (Health Auto Export app)
2. Sharing your Drive folder with our service account so the backend can read it
3. Uploading your config file so the system knows your goals and targets

---

## Step 1 — Create your config file

Go to the setup form and fill out your profile, goal, and targets:

👉 **[Open the setup form](../setup_form.html)**

- Answer the questions that apply to you — leave anything you don't know blank
- Click **Generate my config** at the bottom
- Download the `.json` file (it will be named after you, e.g. `alex.json`)

**Send this file to the admin** (Kurt) — he'll add it to the system. You only need to do this once, or whenever your goals change significantly.

---

## Step 2 — Set up Health Auto Export on iPhone

Health Auto Export is a free iOS app that automatically sends your Apple Health data to Google Drive.

### Install and configure

1. Download **[Health Auto Export](https://apps.apple.com/us/app/health-auto-export-json-csv/id1477944755)** from the App Store (free tier works)
2. Open the app → tap **Automations** → tap **+** to create a new automation
3. Configure the automation:
   - **Export format:** JSON
   - **Destination:** Google Drive
   - **Frequency:** Daily
   - **Folder name:** Create a folder in your Google Drive and set it here — note the exact name (e.g. `Health-exports`). This must match what you entered in your config file.

4. Under **Metrics**, enable at minimum:
   - Body Mass (weight)
   - Heart Rate
   - Heart Rate Variability (HRV)
   - Resting Heart Rate
   - Step Count
   - Active Energy Burned
   - Sleep Analysis
   - Dietary Energy (if you log food)
   - Dietary Protein (if you log food)

5. Under **Workouts**, enable **Workouts** (for workout data)

### Make it actually run reliably

iOS background execution is unreliable. Use these strategies together:

**Best: Add a Shortcuts widget to your home screen**
1. Open the **Shortcuts** app → tap **+** → add a **Run Shortcut** action pointing to Health Auto Export's export action
2. Add this shortcut as a widget on your home screen
3. Tap it once each morning before 7am — takes 2 seconds and guarantees fresh data

**Backup: Plug-in trigger**
1. In the Shortcuts app, create a Personal Automation that fires when you plug your phone in to charge
2. Add a **Run Shortcut** action pointing to the Health Auto Export automation
3. If you charge overnight, this will run automatically most nights

**Also do:**
- Settings → General → Background App Refresh → make sure it's ON for Health Auto Export
- In Health Auto Export → Automations → enable **Retry failed exports**

---

## Step 3 — Share your Google Drive folder with the service account

The backend uses a Google service account to read your health data. You need to give it access to your folder.

### Share your health export folder

1. Open [Google Drive](https://drive.google.com) in a browser
2. Right-click your health export folder (e.g. `Health-exports`) → **Share**
3. In the "Add people" field, enter:
   ```
   fitness-coach-reader@fitness-coach-490102.iam.gserviceaccount.com
   ```
4. Set permission to **Viewer** (read-only is enough)
5. Click **Share** — no email notification needed, it won't receive one

6. If you have a separate workout export folder, share that folder too using the same steps.

> **Note:** The service account can only see folders you explicitly share with it. It cannot see the rest of your Drive.

---

## Step 4 — Tell the admin you're ready

Message Kurt with:
- Your config file (from Step 1), if you haven't sent it already
- The exact name of your Google Drive folder (must match what's in your config)
- Your email address (the one coaching emails should go to)

Once he adds your config, you'll start receiving emails at the next scheduled run.

---

## How the backend finds your data (no chicken-and-egg)

You might wonder: if your config file describes which Drive folder to use, how does the system find your config in the first place?

The answer is that **config discovery and data access are separate steps:**

1. **Config discovery** — The system reads all configs from a central folder (`daily-coach-configs/`) that the admin manages. Your config is placed there when you onboard. This folder never changes — the system always knows where to look first.

2. **Health data access** — Once it has your config, it reads `folder_name` from it (e.g. `"Health-exports"`) and searches Google Drive for a folder with that name that has been shared with the service account. This is when your personal Drive is accessed.

So your config doesn't need to be in your own Drive — it lives in the central registry. Your Drive only needs to contain your health export files, shared with the service account.

---

## What you'll receive

**Morning coaching email** (7:00 AM EDT) — arrives each morning with:
- Yesterday's key metrics vs your targets
- AI coaching brief based on your goals and recent trends
- Streak tracking, rolling averages, countdown to upcoming events

**Evening review email** (6:00 PM EDT) — end-of-day analysis of today's data so far

---

## Keeping your config up to date

Your config is a plain JSON file. Edit it and send an updated version to Kurt whenever:
- Your weight target or deadline changes
- You start training for a new event (add it to `events`)
- You start or stop compounds/medications (add/remove from `compounds`)
- You get bloodwork done (add results to `bloodwork`)
- Your calorie or protein targets change

The form at `setup_form.html` re-generates it cleanly — you don't need to hand-edit the JSON.

---

## Troubleshooting

**Not receiving emails**
- Check your spam folder — add the from address to your contacts
- Confirm your folder was shared with the service account email above
- Confirm the folder name in your config exactly matches the folder name in Google Drive (case-sensitive)

**Data is missing or stale**
- Check that Health Auto Export ran recently — open the app and check the last export time under Automations
- Tap the manual export button (or your home screen shortcut) to force a fresh export
- The system fetches the last 7 days of files, so one missed day won't break anything

**Wrong metrics / targets**
- Send an updated config file to Kurt — he can hot-swap it without downtime
