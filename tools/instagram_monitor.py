"""
JARVIS V7.1 - Public Instagram Monitor

Monitors only publicly accessible Instagram profile pages.
It does not log in, bypass private accounts, bypass CAPTCHAs, or evade
Instagram anti-bot controls.
"""

import json
import re
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None

BASE = Path(__file__).resolve().parents[1]
DATA_FILE = BASE / "data" / "instagram_monitors.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

INSTAGRAM_MONITORS = {}
INSTAGRAM_LOCK = threading.Lock()

DEFAULT_ACCOUNT = "_aan_yeaa_"


def normalize_account(value):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("@"):
        value = value[1:]
    if "instagram.com" in value.lower():
        parsed = urlparse(value if value.startswith("http") else "https://" + value)
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return ""
        value = parts[0]
    value = value.strip("/").split("?")[0].split("#")[0]
    if not re.fullmatch(r"[A-Za-z0-9._]+", value):
        return ""
    return value


def account_url(username):
    return f"https://www.instagram.com/{username}/"


def load_saved():
    if not DATA_FILE.exists():
        return {}
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print("Instagram monitor database error:", e)
        return {}


def save_monitors():
    with INSTAGRAM_LOCK:
        data = {}
        for username, info in INSTAGRAM_MONITORS.items():
            data[username] = {
                "username": username,
                "url": info["url"],
                "interval": info["interval"],
                "fingerprint": info.get("fingerprint"),
                "last_status": info.get("last_status"),
                "last_checked": info.get("last_checked"),
                "last_change": info.get("last_change"),
                "last_posts": info.get("last_posts", []),
            }
    try:
        DATA_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")
    except Exception as e:
        print("Could not save Instagram monitor database:", e)


def fetch_public_profile(username):
    if requests is None:
        return None, "requests is not installed"
    url = account_url(username)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        return response, None
    except requests.RequestException as e:
        return None, str(e)


def extract_public_data(html):
    title_match = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)',
        html, flags=re.IGNORECASE)
    description_match = re.search(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)',
        html, flags=re.IGNORECASE)
    post_ids = sorted(set(re.findall(
        r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
        html, flags=re.IGNORECASE)))
    post_ids += sorted(set(re.findall(
        r'href=["\']/((?:p|reel|tv)/[A-Za-z0-9_-]+)/?["\']',
        html, flags=re.IGNORECASE)))
    normalized_posts = sorted(set(x.strip("/") for x in post_ids))[:100]
    title = re.sub(r"\s+", " ", title_match.group(1) if title_match else "").strip()
    description = re.sub(r"\s+", " ", description_match.group(1) if description_match else "").strip()
    return {"title": title, "description": description, "posts": normalized_posts}


def fingerprint_public_data(data):
    stable = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(stable.encode("utf-8", errors="ignore")).hexdigest()


def alert(username, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 65)
    print("🚨 JARVIS INSTAGRAM ALERT")
    print("Account:", "@" + username)
    print("Change:", message)
    print("Detected:", now)
    print("=" * 65)
    print()
    try:
        from voice.speech import speak
        speak(f"Instagram alert. Public activity changed on the account {username}.")
    except Exception:
        pass


def monitor_worker(username):
    while True:
        with INSTAGRAM_LOCK:
            info = INSTAGRAM_MONITORS.get(username)
            if info is None:
                return
            stop_event = info["stop_event"]
            interval = info["interval"]
        if stop_event.wait(interval):
            return

        response, error = fetch_public_profile(username)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if error:
            became_unavailable = False
            with INSTAGRAM_LOCK:
                if username in INSTAGRAM_MONITORS:
                    previous = INSTAGRAM_MONITORS[username].get("last_status")
                    became_unavailable = previous == "online"
                    INSTAGRAM_MONITORS[username]["last_status"] = "unavailable"
                    INSTAGRAM_MONITORS[username]["last_checked"] = now
            if became_unavailable:
                alert(username, "The public Instagram page is currently unavailable.")
            save_monitors()
            continue

        if response.status_code in (401, 403, 429):
            with INSTAGRAM_LOCK:
                if username in INSTAGRAM_MONITORS:
                    INSTAGRAM_MONITORS[username]["last_status"] = "blocked_or_rate_limited"
                    INSTAGRAM_MONITORS[username]["last_checked"] = now
            print(f"⚠ Instagram public page for @{username} returned HTTP {response.status_code}. JARVIS will not bypass it.")
            save_monitors()
            continue

        if response.status_code >= 400:
            with INSTAGRAM_LOCK:
                if username in INSTAGRAM_MONITORS:
                    INSTAGRAM_MONITORS[username]["last_status"] = "http_error"
                    INSTAGRAM_MONITORS[username]["last_checked"] = now
            save_monitors()
            continue

        public_data = extract_public_data(response.text)
        fingerprint = fingerprint_public_data(public_data)
        first_check = False
        changed = False
        new_posts = []

        with INSTAGRAM_LOCK:
            if username not in INSTAGRAM_MONITORS:
                return
            old_fingerprint = INSTAGRAM_MONITORS[username].get("fingerprint")
            old_posts = INSTAGRAM_MONITORS[username].get("last_posts", [])
            if old_fingerprint is None:
                first_check = True
            elif old_fingerprint != fingerprint:
                changed = True
            new_posts = [post for post in public_data["posts"] if post not in old_posts]
            INSTAGRAM_MONITORS[username]["fingerprint"] = fingerprint
            INSTAGRAM_MONITORS[username]["last_status"] = "online"
            INSTAGRAM_MONITORS[username]["last_checked"] = now
            INSTAGRAM_MONITORS[username]["last_posts"] = public_data["posts"]
            if changed:
                INSTAGRAM_MONITORS[username]["last_change"] = now

        if first_check:
            print()
            print("🟢 INSTAGRAM MONITOR ONLINE")
            print("Account:", "@" + username)
            print("HTTP:", response.status_code)
            print("Public baseline saved:", now)
            print()
        elif changed:
            if new_posts:
                alert(username, f"{len(new_posts)} new public post/reel item(s) detected.")
            else:
                alert(username, "The publicly accessible profile page changed.")
        save_monitors()


def start_instagram_monitor(username, interval=600):
    username = normalize_account(username)
    if not username:
        print("Please give me a valid public Instagram username or URL.")
        return
    if requests is None:
        print("Instagram monitoring needs requests.")
        print("Run: python -m pip install requests")
        return
    try:
        interval = int(interval)
    except Exception:
        interval = 600
    interval = max(60, interval)
    with INSTAGRAM_LOCK:
        if username in INSTAGRAM_MONITORS:
            INSTAGRAM_MONITORS[username]["stop_event"].set()
        INSTAGRAM_MONITORS[username] = {
            "username": username, "url": account_url(username), "interval": interval,
            "fingerprint": None, "last_status": None, "last_checked": None,
            "last_change": None, "last_posts": [], "stop_event": threading.Event(),
        }
    save_monitors()
    thread = threading.Thread(target=monitor_worker, args=(username,), daemon=True, name=f"InstagramMonitor-{username}")
    thread.start()
    print(f"👁 JARVIS is monitoring public Instagram account @{username} every {interval} seconds.")


def stop_instagram_monitor(username):
    username = normalize_account(username)
    with INSTAGRAM_LOCK:
        info = INSTAGRAM_MONITORS.pop(username, None)
        if info:
            info["stop_event"].set()
    save_monitors()
    if info:
        print("🛑 Stopped Instagram monitoring:", "@" + username)
    else:
        print("⚠ I was not monitoring:", "@" + username)


def stop_all_instagram_monitors():
    with INSTAGRAM_LOCK:
        count = len(INSTAGRAM_MONITORS)
        for info in INSTAGRAM_MONITORS.values():
            info["stop_event"].set()
        INSTAGRAM_MONITORS.clear()
    save_monitors()
    print(f"🛑 Stopped {count} Instagram monitor(s)." if count else "No Instagram monitors were active.")


def list_instagram_monitors():
    with INSTAGRAM_LOCK:
        if not INSTAGRAM_MONITORS:
            print("No active Instagram monitors.")
            return
        print()
        print("👁 ACTIVE INSTAGRAM MONITORS")
        print("-" * 70)
        for number, (username, info) in enumerate(INSTAGRAM_MONITORS.items(), 1):
            print(f"{number}. @{username}")
            print(f"   URL: {info['url']}")
            print(f"   Status: {info.get('last_status') or 'waiting'}")
            print(f"   Interval: {info['interval']} seconds")
            print(f"   Last checked: {info.get('last_checked') or 'not checked yet'}")
            if info.get("last_change"):
                print(f"   Last change: {info['last_change']}")
        print("-" * 70)


def restore_instagram_monitors():
    saved = load_saved()
    if not DATA_FILE.exists():
        saved = {
            DEFAULT_ACCOUNT: {
                "username": DEFAULT_ACCOUNT, "url": account_url(DEFAULT_ACCOUNT), "interval": 600,
                "fingerprint": None, "last_status": None, "last_checked": None,
                "last_change": None, "last_posts": [],
            }
        }
    print(f"🔄 Restoring {len(saved)} saved Instagram monitor(s)...")
    for username, info in saved.items():
        username = normalize_account(username)
        if not username:
            continue
        try:
            interval = int(info.get("interval", 600))
        except Exception:
            interval = 600
        interval = max(60, interval)
        with INSTAGRAM_LOCK:
            INSTAGRAM_MONITORS[username] = {
                "username": username, "url": account_url(username), "interval": interval,
                "fingerprint": info.get("fingerprint"), "last_status": info.get("last_status"),
                "last_checked": info.get("last_checked"), "last_change": info.get("last_change"),
                "last_posts": info.get("last_posts", []), "stop_event": threading.Event(),
            }
        threading.Thread(target=monitor_worker, args=(username,), daemon=True, name=f"InstagramMonitor-{username}").start()


def parse_instagram_monitor_command(command):
    pattern = (
        r"^(?:can you |please )?monitor\s+instagram\s+"
        r"(@?[A-Za-z0-9._]+|https?://(?:www\.)?instagram\.com/[A-Za-z0-9._/]+)"
        r"(?:\s+every\s+(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m))?$"
    )
    match = re.match(pattern, command.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    username = normalize_account(match.group(1))
    if not username:
        return None
    amount = match.group(2)
    unit = match.group(3)
    interval = 600
    if amount:
        interval = int(amount)
        if unit.lower().startswith("m"):
            interval *= 60
    return username, max(60, interval)
