# BMS Show Alert

Get woken up **the moment a BookMyShow show opens for booking**, for any movie, cinema, date,
language and format (2D, 3D, IMAX, Dolby Cinema...).

When your show appears, your **Android phone rings a loud alarm**: a spoken announcement with
the showtimes on the alarm channel (works in Do Not Disturb), strong vibration and a
notification. Optionally, it also sends you a **Telegram message** with the showtimes and a
booking link.

It runs on your **Android phone** (recommended) or a **Mac**. No coding needed: you copy a few
commands and fill in a settings file.

---

## Contents

1. [How it works (30 seconds)](#how-it-works)
2. [What you need](#what-you-need)
3. [Step 1: Install the apps on your phone](#step-1-install-the-apps-on-your-phone)
4. [Step 2: Download BMS Show Alert](#step-2-download-bms-show-alert)
5. [Step 3: Copy the cinema link from BookMyShow](#step-3-copy-the-cinema-link-from-bookmyshow)
6. [Step 4: Fill in your settings](#step-4-fill-in-your-settings)
7. [Step 5: Test everything](#step-5-test-everything)
8. [Step 6: Start watching](#step-6-start-watching)
9. [Optional: Telegram messages](#optional-telegram-messages)
10. [All settings explained](#all-settings-explained)
11. [Using it on a Mac](#using-it-on-a-mac)
12. [Troubleshooting](#troubleshooting)
13. [FAQ](#faq)

---

## How it works

Every few minutes (you choose how often) the script opens the BookMyShow page of your cinema
for your date, just like you would in a browser, and looks for your movie in your language and
format.

- If the date **isn't open yet**, BookMyShow quietly shows today's page instead, so the script
  knows to keep waiting.
- When the date **opens** and your show is listed, the alarm goes off right away.
- If more shows are added later, it alerts you again for the new ones.
- It stops by itself after your dates have passed.

> **Why on your phone and not "in the cloud"?** BookMyShow blocks requests from cloud servers
> and from simple scripts. Loading the page in a real browser (Chromium) over your own internet
> connection works, so this tool runs on a device you own.

---

## What you need

- An **Android phone**, kept on charge while watching (or a Mac, see below)
- About **15 minutes** for the first setup
- Optional: **Telegram**, if you also want a message with the showtimes

---

## Step 1: Install the apps on your phone

1. Install **Termux** and **Termux:API** from F-Droid (recommended). Do this on your phone,
   in Chrome:

   | App | Open this page on your phone | Download size |
   |---|---|---|
   | **Termux** | https://f-droid.org/packages/com.termux/ | about 109 MiB |
   | **Termux:API** (needed for the alarm) | https://f-droid.org/en/packages/com.termux.api/ | about 3.8 MiB |

   On each page:
   1. Scroll down to **Packages**. The first version listed is the latest.
   2. Under that latest version, below its list of permissions, tap **Download APK**.
      (You don't need "PGP Signature" or "Build Log".)
   3. Open the downloaded file. If Android asks, allow Chrome to **Install unknown apps**
      (Settings → Apps → Chrome → Install unknown apps → Allow), then tap **Install**.

   Install **Termux first**, then **Termux:API**.

   > **Blocked by Google Play Protect?** Play Protect sometimes blocks or warns about apps
   > installed from outside the Play Store. To install, pause it for a moment:
   > 1. Open the **Play Store** app.
   > 2. Tap your **profile icon** (top right) → **Play Protect** → the **settings gear** (top right).
   > 3. Turn off **Scan apps with Play Protect** (Android may call this "pause").
   > 4. Install Termux and Termux:API.
   > 5. **Turn Play Protect back on** afterwards. It keeps your phone safe, and the installed
   >    apps keep working.

   > **Important:** install both apps from the **same place**. If you already have Termux from
   > Google Play, uninstall it first, or get Termux:API from Google Play too. Mixing sources
   > (one from F-Droid, one from Play) breaks the alarm.

   *The permission lists on those pages (vibration, alarms, keeping the phone awake, storage)
   are normal for these apps; the alarm uses them.*
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

## Step 2: Download BMS Show Alert

In Termux, run these lines one at a time:

```bash
pkg install -y git
git clone https://github.com/mohan0806/bms-show-alert.git
cd bms-show-alert
bash setup_termux.sh
```

`setup_termux.sh` installs everything the tool needs (Python, Chromium, alarm tools) and
creates your settings file. It takes a few minutes; Chromium is a big download.

*Later, to get updates: `cd ~/bms-show-alert && git pull`*

---

## Step 3: Copy the cinema link from BookMyShow

1. Open **BookMyShow** in your phone's browser (Chrome), not the app.
2. Go to the **cinema** you want (search the cinema name, or tap a cinema from any movie).
3. Tap any date at that cinema. The address bar now shows a link like:

   ```
   https://in.bookmyshow.com/cinemas/hyderabad/allu-cinemas-kokapet/buytickets/ALUC/20261112
   ```

4. Copy that whole link. (The date at the end doesn't matter; you set dates separately.)

---

## Step 4: Fill in your settings

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
```

Save and exit: **Ctrl+O**, **Enter**, then **Ctrl+X**.
(On the Termux keyboard, **CTRL** is in the extra key row above the keyboard.)

Tips:

- **MOVIE**: part of the name is enough (`Rama` works), capitals don't matter.
- **LANGUAGE** / **FORMAT**: leave empty to accept any. Use commas for several:
  `FORMAT=IMAX 3D,DOLBY CINEMA 3D`.
- Not sure how BookMyShow spells the format? Step 5 shows you.
- The Telegram lines can stay empty. That's fine.

---

## Step 5: Test everything

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

**c) Test the alarm:**

```bash
python bms_watch.py --test
```

Your phone should speak a test announcement and vibrate. Try it once with the phone in
Do Not Disturb, to be sure it gets through.

---

## Step 6: Start watching

```bash
python bms_watch.py
```

Then:

- **Leave Termux open** and lock your phone. Don't swipe Termux away from recent apps.
- **Keep the phone charging**; loading pages every few minutes uses battery.
- Make sure **Alarms are allowed** in Do Not Disturb / Bedtime mode
  (Settings → Sounds → Do Not Disturb → Alarms: on). Most phones allow alarms by default.
- Keep the **alarm volume up** (the script raises it, but some phones cap it).
- If checks keep failing, you get a **phone notification** saying so.
- To stop: tap the Termux screen and press **Ctrl+C**.

**Watch two things at once?** Make a second settings file and run it in a new Termux
session (swipe from the left edge → New session):

```bash
cp config.env movie2.env && nano movie2.env
python bms_watch.py --config movie2.env
```

---

## Optional: Telegram messages

The alarm is enough on its own. Add Telegram if you also want a message with the
showtimes and a **booking link** you can tap straight away, plus a daily "still running"
message so you know the watcher is alive.

1. Open Telegram and search for **@BotFather** (it has a blue tick).
2. Send it: `/newbot`
3. Give it any name (e.g. `My Movie Alerts`) and a username ending in `bot`
   (e.g. `mohan_movie_alert_bot`).
4. BotFather replies with a **token** like `1234567890:AAH...xyz`.
   **Keep it private**, it's like a password for your bot.
5. Open your new bot (tap the link BotFather gives you) and press **Start**, or send it `hi`.
6. Get your **chat ID**: in a browser, open this link with your token pasted in:

   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```

   Look for `"chat":{"id":` followed by a number, e.g. `"chat":{"id":123456789`.
   That number is your **chat ID**. (If you see `"result":[]`, message your bot again and
   reload the page.)
7. Put both in `config.env`:

   ```ini
   TELEGRAM_BOT_TOKEN=1234567890:AAH...xyz
   TELEGRAM_CHAT_ID=123456789
   ```

8. Run `python bms_watch.py --test`. You should get a Telegram message too.

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
| `PHONE_ALARM` | Loud alarm on the phone / spoken alert on a Mac | `true` |
| `ALARM_ROUNDS` | How many times the alarm repeats (about 6 seconds each) | `15` |
| `TELEGRAM_BOT_TOKEN` | Optional. Your bot token from @BotFather | `1234:AA...` |
| `TELEGRAM_CHAT_ID` | Optional. Your chat ID number | `123456789` |
| `NOTIFY_WHEN_DATE_OPENS` | Notify once when the date opens without your format | `true` |
| `HEARTBEAT_HOUR` | Daily "still running" Telegram message after this hour (India time); empty = off | `9` |
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
   git clone https://github.com/mohan0806/bms-show-alert.git
   cd bms-show-alert
   cp config.example.env config.env
   open -e config.env            # edit, save, close
   python3 bms_watch.py --test
   caffeinate -i python3 bms_watch.py
   ```

`caffeinate -i` stops the Mac from sleeping while it watches. On a Mac the alarm is a spoken
alert through the speakers plus a notification, so keep the volume up (or add Telegram to get
the alert on your phone).

> **iPhone users:** iOS doesn't allow scripts to run in the background, so an iPhone can't do
> the watching. Run the watcher on a Mac or an Android phone, and set up Telegram to get the
> alert on your iPhone.

---

## Troubleshooting

| You see | What it means / fix |
|---|---|
| `No mirror or mirror group selected` | Run `termux-change-repo` (Step 1.5). |
| `CANNOT LINK EXECUTABLE "curl": cannot locate symbol ...` | Termux packages are half-updated. Run `apt update && apt full-upgrade -y`. If that fails, reinstall Termux and Termux:API from F-Droid. |
| `Settings file not found` | Run `cp config.example.env config.env`, then edit it (Step 4). |
| `Settings problem: ...` | The message says which setting is wrong and how to fix it. |
| `BookMyShow returned HTTP 403` | Blocked. Make sure `FETCH_MODE=chromium`. |
| `page title: "Attention Required! \| Cloudflare"` | BookMyShow's bot check blocked the page. Wait 30 to 60 minutes, increase `CHECK_EVERY_SECONDS`, and make sure you're on your home Wi-Fi or mobile data (not a VPN). |
| `Chromium not found` | Run `pkg install x11-repo && pkg install chromium`. |
| Lots of `dbus` / `inotify` error lines | Harmless Chromium noise. Ignore them. |
| `Termux:API tools not found` / no alarm sound | Run `pkg install termux-api`, and install the **Termux:API** app ([F-Droid page](https://f-droid.org/en/packages/com.termux.api/)) from the same source as Termux. |
| "Blocked by Play Protect" / "Unsafe app blocked" | Temporarily turn off Play Protect (Play Store → profile icon → Play Protect → settings gear → Scan apps off), install, then turn it back on. See Step 1. |
| "App not installed" when installing Termux:API | Termux and Termux:API came from different places. Uninstall both and install both from F-Droid (Step 1). |
| Alarm silent in Do Not Disturb | Allow **Alarms** in your Do Not Disturb / Bedtime settings, and turn up the alarm volume. |
| It stopped overnight | Set Termux's battery setting to **Unrestricted**, keep the phone charging, and don't swipe Termux away. |
| `Telegram error 401` | Bot token is wrong. Copy it again from @BotFather (`/mybots` → your bot → API Token). |
| `Telegram error 400` | Chat ID is wrong, or you never pressed Start in your bot. |

---

## FAQ

**Do I need Telegram?** No. The phone alarm works on its own. Telegram just adds a message
with the booking link and a daily "still running" message.

**Is my bot token safe?** It's only stored in `config.env` on your phone. That file is
excluded from git (see `.gitignore`), so it's never uploaded. If you think it leaked, send
`/revoke` to @BotFather and update `config.env`.

**Does it book tickets for me?** No. It only alerts you; you book in the BookMyShow app.

**Does it work for plays, events or sports?** No, only movies listed on a cinema page.

**Can I watch any city or cinema?** Yes. Any BookMyShow cinema page link in India works.

**Is this allowed?** It loads public pages at a slow, human-like pace for personal use.
Keep the interval at 2 minutes or more, don't use it to resell tickets, and respect
BookMyShow's terms of use. BookMyShow can change its website at any time, which may require
an update to this script.

---

MIT License. Not affiliated with BookMyShow.
