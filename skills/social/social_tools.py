import json
import re
import urllib.parse
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
SOCIAL_FILE = DATA / "social_bookmarks.json"

SITES = {
    "instagram": "https://www.instagram.com/",
    "discord": "https://discord.com/app",
    "whatsapp": "https://web.whatsapp.com/",
    "telegram": "https://web.telegram.org/",
    "reddit": "https://www.reddit.com/",
    "x": "https://x.com/",
    "twitter": "https://x.com/",
    "facebook": "https://www.facebook.com/",
    "linkedin": "https://www.linkedin.com/",
    "github": "https://github.com/",
}


def _load():
    if not SOCIAL_FILE.exists():
        return {}
    try:
        return json.loads(SOCIAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data):
    SOCIAL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def open_social(name):
    key = name.strip().lower()
    url = SITES.get(key)
    if not url:
        return False, f"I don't have a launcher for {name} yet."
    webbrowser.open(url)
    return True, f"Opening {name}. Social media has been summoned."


def social_search(platform, query):
    p = platform.lower().strip()
    q = urllib.parse.quote_plus(query.strip())
    urls = {
        "reddit": f"https://www.reddit.com/search/?q={q}",
        "youtube": f"https://www.youtube.com/results?search_query={q}",
        "google": f"https://www.google.com/search?q={q}",
        "github": f"https://github.com/search?q={q}&type=repositories",
    }
    url = urls.get(p)
    if not url:
        return False, "Supported social searches: reddit, youtube, google, github."
    webbrowser.open(url)
    return True, f"Searching {p}."


def save_bookmark(name, url):
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    data = _load()
    data[name.strip().lower()] = url
    _save(data)
    return f"Saved social bookmark '{name.strip()}'."


def list_bookmarks():
    data = _load()
    if not data:
        return "No social bookmarks saved."
    return "Social bookmarks: " + ", ".join(f"{k} = {v}" for k, v in data.items())


def open_bookmark(name):
    data = _load()
    url = data.get(name.strip().lower())
    if not url:
        return f"I couldn't find the bookmark '{name}'."
    webbrowser.open(url)
    return f"Opening bookmarked social destination '{name}'."
