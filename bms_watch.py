#!/usr/bin/env python3
"""
BMS Show Alert: get alerted the moment a BookMyShow show opens for booking.

Watches one or more cinema pages for one or more dates and alerts you when your
movie (optionally in a specific language and format) has shows listed.

Alerts: Telegram message, Telegram voice call (CallMeBot), loud phone alarm (Termux),
or a spoken alert on macOS.

Usage:
  python bms_watch.py            start watching (Ctrl+C to stop)
  python bms_watch.py --list     show which movies, languages and formats are listed
  python bms_watch.py --once     run one check and print the result
  python bms_watch.py --test     send a test Telegram message / call / alarm
  python bms_watch.py --config other.env   use a different settings file

Settings: config.env next to this script (copy config.example.env). See README.md.
Only standard-library Python is needed, plus Chromium (see README).
"""
import datetime
import hashlib
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = "1.0.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MIN_INTERVAL = 60  # be polite to BookMyShow: never check more often than this

DEFAULTS = {
    "CINEMA_URL": "",
    "DATES": "",
    "MOVIE": "",
    "LANGUAGE": "",
    "FORMAT": "",
    "CHECK_EVERY_SECONDS": "150",
    "JITTER_SECONDS": "20",
    "FETCH_MODE": "chromium",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "CALLMEBOT_USER": "",
    "CALLMEBOT_LANG": "en-GB-Standard-B",
    "PHONE_ALARM": "true",
    "ALARM_ROUNDS": "8",
    "NOTIFY_WHEN_DATE_OPENS": "true",
    "HEARTBEAT_HOUR": "9",
    "FAIL_ALERT_AFTER": "5",
    "STOP_AFTER_FOUND": "false",
    "CHROMIUM_PATH": "",
    "STATE_FILE": "",
}
CFG = dict(DEFAULTS)

UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


# --------------------------------------------------------------------------- config

class ConfigError(Exception):
    pass


def load_config(path):
    if not os.path.exists(path):
        raise ConfigError(
            f"Settings file not found: {path}\n"
            "Copy config.example.env to config.env and fill it in (see README, step 5).")
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"{path} line {n}: expected KEY=VALUE, got: {line}")
        k, v = line.split("=", 1)
        k = k.strip().upper()
        v = v.split(" #")[0].strip().strip('"').strip("'")
        if k not in DEFAULTS:
            print(f"Warning: unknown setting {k} in {path} (ignored)")
            continue
        CFG[k] = v


def parse_cinemas():
    urls = [u.strip() for u in re.split(r"[,\s]+", CFG["CINEMA_URL"]) if u.strip()]
    if not urls:
        raise ConfigError("CINEMA_URL is empty. Paste the cinema page link from BookMyShow (README, step 4).")
    out = []
    for u in urls:
        m = re.search(r"bookmyshow\.com/cinemas/([^/]+)/([^/]+)/buytickets/([^/?#]+)", u)
        if not m:
            raise ConfigError(
                f"This doesn't look like a BookMyShow cinema page link:\n  {u}\n"
                "It should look like https://in.bookmyshow.com/cinemas/<city>/<cinema>/buytickets/<CODE>/<date>")
        out.append({"city": m.group(1), "slug": m.group(2), "code": m.group(3)})
    return out


def parse_dates():
    raw = [d.strip() for d in re.split(r"[,\s]+", CFG["DATES"]) if d.strip()]
    if not raw:
        raise ConfigError("DATES is empty. Example: DATES=2026-11-12  (several: 2026-11-12,2026-11-13)")
    dates = []
    for d in raw:
        digits = d.replace("-", "").replace("/", "")
        try:
            datetime.datetime.strptime(digits, "%Y%m%d")
        except ValueError:
            raise ConfigError(f"Bad date '{d}'. Use YYYY-MM-DD, e.g. 2026-11-12")
        dates.append(digits)
    return sorted(set(dates))


def as_list(value):
    return [norm(x) for x in value.split(",") if x.strip()]


def validate():
    cinemas, dates = parse_cinemas(), parse_dates()
    if not CFG["MOVIE"].strip():
        raise ConfigError("MOVIE is empty. Example: MOVIE=Ramayana")
    if int(CFG["CHECK_EVERY_SECONDS"]) < MIN_INTERVAL:
        print(f"Note: CHECK_EVERY_SECONDS raised to {MIN_INTERVAL} (minimum, to avoid getting blocked).")
        CFG["CHECK_EVERY_SECONDS"] = str(MIN_INTERVAL)
    return cinemas, dates


# --------------------------------------------------------------------------- helpers

def norm(s):
    return " ".join(str(s or "").upper().split())


def log(*a):
    print(datetime.datetime.now().strftime("%d %b %H:%M:%S"), *a, flush=True)


def today_ist():
    return datetime.datetime.now(IST).strftime("%Y%m%d")


def pretty_date(code):
    return datetime.datetime.strptime(code, "%Y%m%d").strftime("%a %d %b")


def page_url(cinema, date):
    return (f"https://in.bookmyshow.com/cinemas/{cinema['city']}/{cinema['slug']}"
            f"/buytickets/{cinema['code']}/{date}")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def target_label():
    bits = [CFG["MOVIE"]]
    if CFG["LANGUAGE"]:
        bits.append(CFG["LANGUAGE"])
    if CFG["FORMAT"]:
        bits.append(CFG["FORMAT"])
    return " / ".join(bits)


# --------------------------------------------------------------------------- state

def state_path():
    if CFG["STATE_FILE"]:
        return os.path.expanduser(CFG["STATE_FILE"])
    key = "|".join([CFG["CINEMA_URL"], CFG["DATES"], CFG["MOVIE"], CFG["LANGUAGE"], CFG["FORMAT"]])
    return os.path.join(SCRIPT_DIR, f".state-{hashlib.sha1(key.encode()).hexdigest()[:10]}.json")


def load_state():
    try:
        return json.load(open(state_path()))
    except Exception:
        return {"alerted": [], "date_open": [], "fails": 0, "heartbeat": "", "found_any": False}


def save_state(st):
    json.dump(st, open(state_path(), "w"))


# --------------------------------------------------------------------------- fetching

def parse_html(html, how):
    m = re.search(r"window\.__INITIAL_STATE__\s*=\s*([\s\S]*?)</script>", html)
    if not m:
        title = re.search(r"<title>([^<]*)", html)
        hint = f' (page title: "{title.group(1).strip()}")' if title else ""
        raise RuntimeError(f"No showtime data in the page via {how}{hint}. Possibly blocked by a bot check.")
    return json.loads(m.group(1).strip().rstrip(";"))


def find_chromium():
    if CFG["CHROMIUM_PATH"]:
        return CFG["CHROMIUM_PATH"]
    for name in ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable"):
        if shutil.which(name):
            return shutil.which(name)
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac):
        return mac
    return None


def fetch_chromium(url):
    exe = find_chromium()
    if not exe:
        raise RuntimeError("Chromium not found. On Termux: pkg install x11-repo && pkg install chromium")
    # These exact options are verified to get through on Termux. Note: plain "--headless",
    # not "--headless=new", and a normal phone user agent (headless Chrome's default is blocked).
    r = subprocess.run([exe, "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                        f"--user-agent={UA}", "--dump-dom", url],
                       capture_output=True, text=True, timeout=120)
    if not r.stdout.strip():
        raise RuntimeError("Chromium returned an empty page (it may have crashed; try again).")
    return parse_html(r.stdout, "chromium")


def fetch_plain(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-IN,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return parse_html(r.read().decode("utf-8", "replace"), "plain request")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"BookMyShow returned HTTP {e.code}")


def fetch_state(url):
    mode = CFG["FETCH_MODE"].lower()
    if mode == "plain":
        return fetch_plain(url)
    if mode == "auto":
        try:
            return fetch_plain(url)
        except RuntimeError:
            return fetch_chromium(url)
    return fetch_chromium(url)


# --------------------------------------------------------------------------- parsing

def extract(state, date):
    """Return the page's date status and every movie/language/format with its shows."""
    queries = ((state or {}).get("venueShowtimesFunctionalApi") or {}).get("queries") or {}
    q = next((x for x in queries.values()
              if isinstance(x, dict) and (x.get("data") or {}).get("showDetailsTransformed")), None)
    if not q:
        raise RuntimeError("BookMyShow page layout changed: showtimes not found. The script needs an update.")
    d = q["data"]
    t = d["showDetailsTransformed"]
    served = str(t.get("Date"))
    entry = next((x for x in d.get("ShowDatesArray") or [] if x.get("DateCode") == date), None)
    # A date that isn't open yet redirects to today's page, so "served == date" means open.
    is_open = served == date or (entry is not None and entry.get("isDisabled") is False)
    listings = []
    for ev in t.get("Event") or []:
        for ch in ev.get("ChildEvents") or []:
            listings.append({
                "movie": ev.get("EventTitle", ""),
                "language": ch.get("EventLanguage", ""),
                "format": ch.get("EventDimension", ""),
                "shows": [{"time": s.get("ShowTime"), "screen": s.get("ScreenName") or "",
                           "id": str(s.get("SessionId")), "min": s.get("MinPrice"), "max": s.get("MaxPrice")}
                          for s in ch.get("ShowTimes") or []],
            })
    venue = (t.get("Venues") or {}).get("VenueName") or ""
    return {"served_date": served, "is_open": is_open, "venue": venue, "listings": listings,
            "date_known": entry is not None}


def matches(listing):
    if norm(CFG["MOVIE"]) not in norm(listing["movie"]):
        return False
    langs, fmts = as_list(CFG["LANGUAGE"]), as_list(CFG["FORMAT"])
    if langs and norm(listing["language"]) not in langs:
        return False
    if fmts and norm(listing["format"]) not in fmts:
        return False
    return True


def check(cinema, date):
    info = extract(fetch_state(page_url(cinema, date)), date)
    shows, others = [], set()
    if info["served_date"] == date:
        for l in info["listings"]:
            if matches(l):
                for s in l["shows"]:
                    shows.append({**s, "language": l["language"], "format": l["format"]})
            elif norm(CFG["MOVIE"]) in norm(l["movie"]):
                others.add(f"{l['language']} {l['format']}")
    return {**info, "shows": shows, "other_formats": sorted(others)}


# --------------------------------------------------------------------------- alerts

def telegram(text):
    tok, chat = CFG["TELEGRAM_BOT_TOKEN"], CFG["TELEGRAM_CHAT_ID"]
    if not tok or not chat:
        log("(Telegram not set up, message not sent)")
        return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=30).read()
        return True
    except urllib.error.HTTPError as e:
        hint = {401: "bot token is wrong", 400: "chat ID is wrong, or you never messaged the bot"}.get(e.code, "")
        log(f"Telegram error {e.code} {hint}")
    except Exception as e:
        log("Telegram error:", e)
    return False


def phone_call(text):
    user = CFG["CALLMEBOT_USER"]
    if not user:
        return
    qs = urllib.parse.urlencode({"user": user, "text": text, "lang": CFG["CALLMEBOT_LANG"], "rpt": "3"})
    try:
        urllib.request.urlopen(f"https://api.callmebot.com/start.php?{qs}", timeout=60).read()
        log("Telegram voice call requested (CallMeBot)")
    except Exception as e:
        log("CallMeBot call failed:", e)


def _run(*args):
    try:
        subprocess.run(args, timeout=60, capture_output=True)
    except Exception:
        pass


def alarm(text, rounds=None):
    if CFG["PHONE_ALARM"].lower() != "true":
        return
    rounds = rounds or int(CFG["ALARM_ROUNDS"])
    if shutil.which("termux-tts-speak"):  # Android (Termux:API)
        _run("termux-notification", "--id", "bms", "--title", "BOOKING OPEN", "--content", text,
             "--priority", "max", "--sound", "--vibrate", "1000,500,1000,500,1000")
        _run("termux-volume", "alarm", "15")
        for _ in range(rounds):
            _run("termux-vibrate", "-f", "-d", "2000")
            _run("termux-tts-speak", "-s", "ALARM", "-r", "0.9", text)
            time.sleep(1)
    elif platform.system() == "Darwin" and shutil.which("say"):  # macOS
        _run("osascript", "-e", f'display notification "{text}" with title "BOOKING OPEN"')
        for _ in range(rounds):
            _run("say", text)
    else:
        for _ in range(rounds):
            print("\a*** BOOKING OPEN ***", text, flush=True)
            time.sleep(1)


def alert_found(result, cinema, date, fresh_ids):
    lines = []
    for s in result["shows"]:
        price = ""
        try:
            if s["min"]:
                lo, hi = round(float(s["min"])), round(float(s["max"] or s["min"]))
                price = f" (Rs {lo}" + (f"-{hi}" if hi != lo else "") + ")"
        except ValueError:
            pass
        tag = "NEW " if s["id"] in fresh_ids else ""
        lines.append(f"{tag}{esc(s['time'])} {esc(s['language'])} {esc(s['format'])}"
                     + (f" - {esc(s['screen'])}" if s["screen"] else "") + price)
    url = page_url(cinema, date)
    telegram(f"<b>BOOKING OPEN: {esc(target_label())}</b>\n{pretty_date(date)}, {esc(result['venue'])}\n\n"
             + "\n".join(lines) + f'\n\n<a href="{url}">Book now on BookMyShow</a>')
    times = ", ".join(sorted({s["time"] for s in result["shows"] if s["id"] in fresh_ids}))
    speech = f"Booking open. {CFG['MOVIE']}. {pretty_date(date)}. Shows at {times}."
    phone_call(speech)
    alarm(speech)


# --------------------------------------------------------------------------- commands

def cmd_list(cinemas, dates):
    for c in cinemas:
        for d in dates:
            info = extract(fetch_state(page_url(c, d)), d)
            print(f"\n=== {info['venue'] or c['slug']} | {pretty_date(d)} ===")
            if info["served_date"] != d:
                print(f"Not open for booking yet. BookMyShow showed {pretty_date(info['served_date'])} instead,")
                print("listed below so you can copy the exact LANGUAGE / FORMAT spelling:")
            by_movie = {}
            for l in info["listings"]:
                by_movie.setdefault(l["movie"], []).append(l)
            for movie, ls in by_movie.items():
                print(f"\n  MOVIE: {movie}")
                for l in ls:
                    print(f"    LANGUAGE={l['language']:<10} FORMAT={l['format']:<18} ({len(l['shows'])} shows)")
    print()


def cmd_once(cinemas, dates):
    for c in cinemas:
        for d in dates:
            r = check(c, d)
            print(json.dumps({"cinema": r["venue"] or c["slug"], "date": d, "date_open": r["is_open"],
                              "page_showed_date": r["served_date"], "matching_shows": r["shows"],
                              "other_formats_of_movie": r["other_formats"]}, indent=2))


def cmd_test():
    ok = telegram(f"Test from BMS Show Alert. Telegram works.\nWatching: {esc(target_label())}")
    print("Telegram:", "sent" if ok else "NOT sent (see message above)")
    if CFG["CALLMEBOT_USER"]:
        phone_call("This is a test call from BMS Show Alert.")
    alarm("This is a test alarm from BMS Show Alert.", rounds=2)
    print("Test finished.")


def watch(cinemas, dates):
    st = load_state()
    interval, jitter = int(CFG["CHECK_EVERY_SECONDS"]), int(CFG["JITTER_SECONDS"])
    fail_after = int(CFG["FAIL_ALERT_AFTER"])
    if shutil.which("termux-wake-lock"):
        _run("termux-wake-lock")
    log(f"BMS Show Alert {VERSION}: watching {target_label()} | {len(cinemas)} cinema(s) | "
        f"dates {', '.join(pretty_date(d) for d in dates)} | every ~{interval}s. Ctrl+C to stop.")

    while True:
        active = [d for d in dates if d >= today_ist()]
        if not active:
            log("All dates have passed. Stopping.")
            telegram(f"BMS Show Alert stopped: all dates for {esc(target_label())} have passed.")
            break
        for c in cinemas:
            for d in active:
                try:
                    r = check(c, d)
                except Exception as e:
                    st["fails"] += 1
                    log(f"check failed ({st['fails']} in a row): {e}")
                    n = st["fails"]
                    if n == fail_after or (n > fail_after and (n - fail_after) % 25 == 0):
                        telegram(f"<b>BMS Show Alert problem:</b> {n} checks in a row failed.\n{esc(e)}")
                    continue
                st["fails"] = 0
                key = f"{c['code']}:{d}"
                log(f"{c['slug']} {d}: open={r['is_open']} matching_shows={len(r['shows'])}")
                if r["shows"]:
                    seen = set(st["alerted"])
                    fresh = {f"{key}:{s['id']}" for s in r["shows"]} - seen
                    if fresh:
                        alert_found(r, c, d, {x.rsplit(':', 1)[1] for x in fresh})
                        st["alerted"] = sorted(seen | fresh)
                        st["found_any"] = True
                elif r["is_open"] and key not in st["date_open"] and CFG["NOTIFY_WHEN_DATE_OPENS"].lower() == "true":
                    others = ", ".join(r["other_formats"]) or "no shows of this movie yet"
                    telegram(f"<b>{pretty_date(d)} booking is open</b> at {esc(r['venue'])}, but nothing matches "
                             f"{esc(target_label())} yet. Still watching.\nOther formats: {esc(others)}\n\n"
                             f'<a href="{page_url(c, d)}">Open BookMyShow</a>')
                    st["date_open"].append(key)
                save_state(st)
                time.sleep(random.uniform(2, 6))  # small gap between pages

        hb = CFG["HEARTBEAT_HOUR"].strip()
        now = datetime.datetime.now(IST)
        if hb and now.hour >= int(hb) and st["heartbeat"] != now.strftime("%Y%m%d"):
            telegram(f"BMS Show Alert is running: {esc(target_label())}, "
                     f"{', '.join(pretty_date(d) for d in active)}. Nothing yet.")
            st["heartbeat"] = now.strftime("%Y%m%d")
        save_state(st)

        if st["found_any"] and CFG["STOP_AFTER_FOUND"].lower() == "true":
            log("Found shows and STOP_AFTER_FOUND=true. Stopping.")
            break
        time.sleep(max(MIN_INTERVAL, interval + random.randint(-jitter, jitter)))
    if shutil.which("termux-wake-unlock"):
        _run("termux-wake-unlock")


def main():
    args = sys.argv[1:]
    cfg_path = os.path.join(SCRIPT_DIR, "config.env")
    if "--config" in args:
        i = args.index("--config")
        cfg_path = os.path.expanduser(args[i + 1])
    if "--version" in args:
        print(VERSION)
        return
    try:
        load_config(cfg_path)
        if "--test" in args:
            cmd_test()
            return
        cinemas, dates = validate()
        if "--list" in args:
            cmd_list(cinemas, dates)
        elif "--once" in args:
            cmd_once(cinemas, dates)
        else:
            watch(cinemas, dates)
    except ConfigError as e:
        print(f"\nSettings problem:\n{e}\n")
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
