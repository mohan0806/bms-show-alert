# BMS Show Alert

Get alerted **the moment a BookMyShow show opens for booking**, for any movie, cinema, date,
language and format (2D, 3D, IMAX, Dolby Cinema...).

When your show appears, you get:

- a **Telegram message** with the showtimes, prices and a booking link,
- an optional **Telegram voice call** (so it wakes you up at night),
- a **loud alarm** on your Android phone (or a spoken alert on a Mac).

It runs on your **Android phone** (recommended) or a **Mac**. No coding needed: you copy a few
commands and fill in a settings file.

---

## Contents

1. [How it works (30 seconds)](#how-it-works)
2. [What you need](#what-you-need)
3. [Step 1: Create your Telegram bot](#step-1-create-your-telegram-bot)
4. [Step 2: Install the apps on your phone](#step-2-install-the-apps-on-your-phone)
5. [Step 3: Download BMS Show Alert](#step-3-download-bms-show-alert)
6. [Step 4: Copy the cinema link from BookMyShow](#step-4-copy-the-cinema-link-from-bookmyshow)
7. [Step 5: Fill in your settings](#step-5-fill-in-your-settings)
8. [Step 6: Test everything](#step-6-test-everything)
9. [Step 7: Start watching](#step-7-start-watching)
10. [Optional: Telegram wake-up call](#optional-telegram-wake-up-call)
11. [All settings explained](#all-settings-explained)
12. [Using it on a Mac](#using-it-on-a-mac)
13. [Troubleshooting](#troubleshooting)
14. [FAQ](#faq)

---

## How it works

Every few minutes (you choose how often) the script opens the BookMyShow page of your cinema
for your date, just like you would in a browser, and looks for your movie in your language and
format.

- If the date **isn't open yet**, BookMyShow quietly shows today's page instead, so the script
  knows to keep waiting.
- When the date **opens** and your show is listed, it alerts you right away.
- If more shows are added later, you get another alert for the new ones.
- It stops by itself after your dates have passed.

> **Why on your phone and not "in the cloud"?** BookMyShow blocks requests from cloud servers
> and from simple scripts. Loading the page in a real browser (Chromium) over your own internet
> connection works, so this tool runs on a device you own.

---

## What you need

- An **Android phone** (kept on charge while watching), or a Mac
- **Telegram** on your phone
- About **15 minutes** for the first setup

---

## Step 1: Create your Telegram bot

The bot is what sends you messages. It's free and takes 2 minutes.

1. Open Telegram and search for **@BotFather** (it has a blue tick).
2. Send it: `/newbot`
3. Give it any name (e.g. `My Movie Alerts`) and a username ending in `bot`
   (e.g. `mohan_movie_alert_bot`).
4. BotFather replies with a **token** like `1234567890:AAH...xyz`.
   **Copy it and keep it private**, it's like a password for your bot.
5. Open your new bot (tap the link BotFather gives you) and press **Start**, or send it `hi`.
6. Get your **chat ID**: in a browser, open this link with your token pasted in:

   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```

   Look for `"chat":{"id":` followed by a number, e.g. `"chat":{"id":871230075`.
   That number is your **chat ID**.

   *If you see `"result":[]`, send your bot another message and reload the page.*

---

## Step 2: Install the apps on your phone

1. Install **Termux** and **Termux:API**.
   - Get both from **F-Droid** (https://f-droid.org), **or** both from Google Play.
   - **Don't mix sources** (one from F-Droid, one from Play). That breaks the alarm features.
2. Stop Android from killing it at night:
   **Settings → Apps → Termux → Battery → Unrestricted**. Do the same for **Termux:API**.
3. Allow notifications for Termux when asked.
4. Open **Termux**. You'll see a black screen with `~ $`. That's where you type commands.
   (Tip: long-press in Termux to paste.)
5. Pick a download server (fixes "No mirror selected" errors). Run:

   ```bash
   termux-change-repo
   ```

   Use the arrow keys and **Space** to pick **Mirror group**, press **Enter**, choose any
   group (e.g. Asia), then **Enter** again.

---

## Step 3: Download BMS Show Alert

In Termux, run these lines one at a time:

```bash
pkg install -y git
git clone https://github.com/<your-github-username>/bms-show-alert.git
cd bms-show-alert
bash setup_termux.sh
```

`setup_termux.sh` installs everything the tool needs (Python, Chromium, alarm tools) and
creates your settings file. It takes a few minutes; Chromium is a big download.

*Later, to get updates: `cd ~/bms-show-alert && git pull`*

---

## Step 4: Copy the cinema link from BookMyShow

1. Open **BookMyShow** in your phone's browser (Chrome), not the app.
2. Go to the **cinema** you want (search the cinema name, or tap a cinema from any movie).
3. Tap any date at that cinema. The address bar now shows a link like:

   ```
   https://in.bookmyshow.com/cinemas/hyderabad/allu-cinemas-kokapet/buytickets/ALUC/20261112
   ```

4. Copy that whole link. (The date at the end doesn't matter; you set dates separately.)

---

## Step 5: Fill in your settings

In Termux:

```bash
nano config.env
```

This opens a simple text editor. Move with the arrow keys and change the values after `=`:

```ini
CINEMA_URL=https://in.bookmyshow.com/cinemas/hyderabad/allu-cinemas-kokapet/buytickets/ALUC/20261112
DATES=2026-11-12
MOVIE=Ramayana
LANGUAGE=Telugu
FORMAT=DOLBY CINEMA 3D
CHECK_EVERY_SECONDS=150
TELEGRAM_BOT_TOKEN=1234567890:AAH...xyz
TELEGRAM_CHAT_ID=871230075
```

Save and exit: **Ctrl+O**, **Enter**, then **Ctrl+X**.
(On the Termux keyboard, **CTRL** is in the extra key row above the keyboard.)

Tips:

- **MOVIE**: part of the name is enough (`Rama` works), capitals don't matter.
- **LANGUAGE** / **FORMAT**: leave empty to accept any. Use commas for several:
  `FORMAT=IMAX 3D,DOLBY CINEMA 3D`.
- Not sure how BookMyShow spells the format? Step 6 shows you.

---

## Step 6: Test everything

**a) See what's listed** (and copy the exact spellings):

```bash
python bms_watch.py --list
```

Example output:

```
=== ALLU Cinemas: Kokapet | Thu 12 Nov ===
  MOVIE: Ramayana
    LANGUAGE=Telugu     FORMAT=DOLBY CINEMA 3D    (3 shows)
    LANGUAGE=Hindi      FORMAT=3D                 (2 shows)
```

If your date isn't open yet, it lists today's shows instead, so you can still copy the
format names.

**b) Run one check:**

```bash
python bms_watch.py --once
```

`"date_open": false` means "not open yet, keep waiting". That's normal.

**c) Test your alerts:**

```bash
python bms_watch.py --test
```

You should get a Telegram message and hear the alarm.

---

## Step 7: Start watching

```bash
python bms_watch.py
```

Then:

- **Leave Termux open** and lock your phone. Don't swipe Termux away from recent apps.
- **Keep the phone charging**; loading pages every few minutes uses battery.
- Make sure **Alarms are allowed** in Do Not Disturb / Bedtime mode
  (Settings → Sounds → Do Not Disturb → Alarms: on).
- You get a short **"still running"** Telegram message each day, so you know it's alive.
- To stop: tap the Termux screen and press **Ctrl+C**.

**Watch two things at once?** Make a second settings file and run it in a new Termux
session (swipe from the left edge → New session):

```bash
cp config.env movie2.env && nano movie2.env
python bms_watch.py --config movie2.env
```

---

## Optional: Telegram wake-up call

[CallMeBot](https://www.callmebot.com) can **phone you on Telegram** and read out the showtimes,
which wakes you up better than a notification.

1. On callmebot.com, open **Telegram Call API** and follow the one-time steps there to let
   CallMeBot call your Telegram account. (Your Telegram account needs a **username**:
   Telegram → Settings → Username.)
2. In `config.env`, set `CALLMEBOT_USER=@yourusername`
3. Run `python bms_watch.py --test`. Your phone should ring on Telegram.
4. Allow Telegram calls through Do Not Disturb.

---

## All settings explained

| Setting | What it does | Example |
|---|---|---|
| `CINEMA_URL` | Cinema page link(s) from BookMyShow. Comma-separate for several cinemas. | `https://in.bookmyshow.com/cinemas/...` |
| `DATES` | Date(s) to book, YYYY-MM-DD, comma-separated | `2026-11-12,2026-11-13` |
| `MOVIE` | Movie name, or part of it | `Ramayana` |
| `LANGUAGE` | Language(s); empty = any | `Telugu` |
| `FORMAT` | Format(s), exactly as `--list` shows; empty = any | `DOLBY CINEMA 3D` |
| `CHECK_EVERY_SECONDS` | Seconds between checks (minimum 60) | `150` |
| `JITTER_SECONDS` | Random +/- added to each wait | `20` |
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather | `1234:AA...` |
| `TELEGRAM_CHAT_ID` | Your chat ID number | `871230075` |
| `CALLMEBOT_USER` | Your Telegram @username for wake-up calls; empty = off | `@mohan` |
| `PHONE_ALARM` | Loud alarm on the phone / spoken alert on a Mac | `true` |
| `ALARM_ROUNDS` | How many times the alarm repeats | `8` |
| `NOTIFY_WHEN_DATE_OPENS` | Tell you once when the date opens without your format | `true` |
| `HEARTBEAT_HOUR` | Daily "still running" message after this hour (India time); empty = off | `9` |
| `FAIL_ALERT_AFTER` | Warn after this many failed checks in a row | `5` |
| `STOP_AFTER_FOUND` | Stop after the first alert (`true`) or keep watching for new shows (`false`) | `false` |
| `FETCH_MODE` | `chromium` (recommended), `auto`, or `plain` | `chromium` |
| `CHROMIUM_PATH` | Only if Chromium/Chrome isn't found automatically | |

**Choosing how often to check:** every 2 to 5 minutes is plenty. Checking more often than
that doesn't help much and makes it more likely BookMyShow blocks you. With several cinemas
and dates, each check loads one page per cinema per date, so use a longer interval.

---

## Using it on a Mac

Useful as a second watcher while your Mac is awake (it doesn't work while the Mac sleeps).

1. Install **Google Chrome** (the script finds it automatically).
2. In the **Terminal** app:

   ```bash
   git clone https://github.com/<your-github-username>/bms-show-alert.git
   cd bms-show-alert
   cp config.example.env config.env
   open -e config.env            # edit, save, close
   python3 bms_watch.py --test
   caffeinate -i python3 bms_watch.py
   ```

`caffeinate -i` stops the Mac from sleeping while it watches. On a Mac the "alarm" is a
spoken alert through the speakers, so rely on Telegram (and the wake-up call) on your phone.

> **iPhone users:** iOS doesn't allow scripts to run in the background, so the iPhone can't
> do the watching. Run the watcher on a Mac or an Android phone; your iPhone still gets the
> Telegram message and call.

---

## Troubleshooting

| You see | What it means / fix |
|---|---|
| `No mirror or mirror group selected` | Run `termux-change-repo` (Step 2.5). |
| `CANNOT LINK EXECUTABLE "curl": cannot locate symbol ...` | Termux packages are half-updated. Run `apt update && apt full-upgrade -y`. If that fails, reinstall Termux and Termux:API from F-Droid. |
| `cp: cannot stat '.../storage/downloads/...'` | Termux has no storage access. Run `termux-setup-storage` and tap Allow. |
| `Settings file not found` | Run `cp config.example.env config.env`, then edit it (Step 5). |
| `Settings problem: ...` | The message says which setting is wrong and how to fix it. |
| `BookMyShow returned HTTP 403` | Blocked. Make sure `FETCH_MODE=chromium`. |
| `page title: "Attention Required! \| Cloudflare"` | BookMyShow's bot check blocked the page. Wait 30 to 60 minutes, increase `CHECK_EVERY_SECONDS`, and make sure you're on your home Wi-Fi or mobile data (not a VPN). |
| `Chromium not found` | Run `pkg install x11-repo && pkg install chromium`. |
| Lots of `dbus` / `inotify` error lines | Harmless Chromium noise. Ignore them. |
| `Telegram error 401` | Bot token is wrong. Copy it again from @BotFather (`/mybots` → your bot → API Token). |
| `Telegram error 400` | Chat ID is wrong, or you never pressed Start in your bot. |
| No alarm sound | Install **Termux:API** from the same source as Termux, and allow Alarms in Do Not Disturb. |
| It stopped overnight | Set Termux's battery setting to **Unrestricted**, keep the phone charging, and don't swipe Termux away. |

---

## FAQ

**Is my bot token safe?** It's only stored in `config.env` on your phone. That file is
excluded from git (see `.gitignore`), so it's never uploaded. Never paste your token in
public chats. If you think it leaked, send `/revoke` to @BotFather and update `config.env`.

**Does it book tickets for me?** No. It only alerts you; you book in the BookMyShow app.

**Does it work for plays, events or sports?** No, only movies listed on a cinema page.

**Can I watch any city or cinema?** Yes. Any BookMyShow cinema page link in India works.

**Is this allowed?** It loads public pages at a slow, human-like pace for personal use.
Keep the interval at 2 minutes or more, don't use it to resell tickets, and respect
BookMyShow's terms of use. BookMyShow can change its website at any time, which may require
an update to this script.

---

MIT License. Not affiliated with BookMyShow.
