import json
import re
import hashlib
import threading
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

from core.memory import Memory
from core.automation import Automation
from tools.apps import open_app
from tools.browser import open_website, web_search, youtube_search
from tools.files import search_files, open_path
from tools.system import system_info, defender_status
from voice.speech import speak
from voice.recognition import listen

try:
    from tools.instagram_monitor import (
        start_instagram_monitor,
        stop_instagram_monitor,
        stop_all_instagram_monitors,
        list_instagram_monitors,
        restore_instagram_monitors,
        parse_instagram_monitor_command,
    )
except Exception:
    start_instagram_monitor = None
    stop_instagram_monitor = None
    stop_all_instagram_monitors = None
    list_instagram_monitors = None
    restore_instagram_monitors = None
    parse_instagram_monitor_command = None

try:
    from updater import check_and_apply_updates
except Exception:
    check_and_apply_updates = None

try:
    from core.ai import JARVISAI
except Exception:
    JARVISAI = None

BASE = Path(__file__).resolve().parent
CONFIG_FILE = BASE / "config.json"
MEMORY_FILE = BASE / "data" / "memory.json"
AUTOMATION_FILE = BASE / "data" / "automations.json"
MONITOR_FILE = BASE / "data" / "website_monitors.json"

(BASE / "data").mkdir(parents=True, exist_ok=True)

CONFIG = {}
AI = None
memory = None
automation = None

MONITORS = {}
MONITOR_LOCK = threading.Lock()


def load_config():
    if not CONFIG_FILE.exists():
        return {"api_key": "", "model": "", "voice": True}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print("Config error:", e)
        return {"api_key": "", "model": "", "voice": True}


def setup():
    global CONFIG, AI, memory, automation
    CONFIG = load_config()
    try:
        memory = Memory(str(MEMORY_FILE))
    except Exception as e:
        print("Memory system unavailable:", e)
    try:
        automation = Automation(str(AUTOMATION_FILE))
    except Exception as e:
        print("Automation system unavailable:", e)
    if JARVISAI and CONFIG.get("api_key"):
        try:
            AI = JARVISAI(
                api_key=CONFIG["api_key"],
                model=CONFIG.get("model", "openrouter/free")
            )
        except Exception as e:
            print("AI unavailable:", e)


def normalize_url(url):
    url = url.strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    return url


def clean_page(html):
    html = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style\b[^>]*>.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def page_fingerprint(html):
    text = clean_page(html)
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def load_saved_monitors():
    if not MONITOR_FILE.exists():
        return {}
    try:
        data = json.loads(MONITOR_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as e:
        print("Monitor database error:", e)
    return {}


def save_monitors():
    with MONITOR_LOCK:
        data = {}
        for url, info in MONITORS.items():
            data[url] = {
                "url": url,
                "interval": info["interval"],
                "last_status": info.get("last_status"),
                "last_checked": info.get("last_checked"),
                "last_change": info.get("last_change")
            }
    try:
        MONITOR_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")
    except Exception as e:
        print("Could not save monitor database:", e)


def fetch_page(url):
    if requests is None:
        return None, "requests is not installed"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/140 Safari/537.36 "
            "JARVIS-Website-Monitor/1.0"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        return response, None
    except requests.RequestException as e:
        return None, str(e)


def monitor_worker(url):
    while True:
        with MONITOR_LOCK:
            info = MONITORS.get(url)
            if info is None:
                return
            stop_event = info["stop_event"]
            interval = info["interval"]
        if stop_event.wait(interval):
            return
        response, error = fetch_page(url)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if error:
            became_offline = False
            with MONITOR_LOCK:
                if url in MONITORS:
                    previous = MONITORS[url].get("last_status")
                    became_offline = previous == "online"
                    MONITORS[url]["last_status"] = "offline"
                    MONITORS[url]["last_checked"] = now
            if became_offline:
                print()
                print("=" * 60)
                print("🚨 JARVIS WEBSITE ALERT")
                print("WEBSITE APPEARS OFFLINE")
                print("URL:", url)
                print("Time:", now)
                print("=" * 60)
                print()
            save_monitors()
            continue
        fingerprint = page_fingerprint(response.text)
        first_check = False
        changed = False
        with MONITOR_LOCK:
            if url not in MONITORS:
                return
            old_fingerprint = MONITORS[url].get("fingerprint")
            if old_fingerprint is None:
                first_check = True
            elif old_fingerprint != fingerprint:
                changed = True
            MONITORS[url]["fingerprint"] = fingerprint
            MONITORS[url]["last_status"] = "online"
            MONITORS[url]["last_checked"] = now
            if changed:
                MONITORS[url]["last_change"] = now
        if first_check:
            print()
            print("🟢 WEBSITE MONITOR ONLINE")
            print("URL:", url)
            print("HTTP:", response.status_code)
            print("Baseline saved:", now)
            print()
        elif changed:
            print()
            print("=" * 60)
            print("🚨 [JARVIS MONITOR] WEBSITE CHANGED")
            print("URL:", url)
            print("HTTP:", response.status_code)
            print("Detected:", now)
            print("=" * 60)
            print()
        save_monitors()


def start_monitor(url, interval=60):
    url = normalize_url(url)
    if not url:
        print("Please give me a URL.")
        return
    try:
        interval = int(interval)
    except Exception:
        interval = 60
    interval = max(15, interval)
    if requests is None:
        print()
        print("Website monitoring needs requests.")
        print("Run:")
        print("python -m pip install requests")
        print()
        return
    with MONITOR_LOCK:
        if url in MONITORS:
            MONITORS[url]["stop_event"].set()
        MONITORS[url] = {
            "url": url,
            "interval": interval,
            "fingerprint": None,
            "last_status": None,
            "last_checked": None,
            "last_change": None,
            "stop_event": threading.Event()
        }
    save_monitors()
    thread = threading.Thread(target=monitor_worker, args=(url,), daemon=True)
    thread.start()
    print(f"👁 JARVIS is monitoring {url} every {interval} seconds.")


def stop_monitor(url):
    url = normalize_url(url)
    with MONITOR_LOCK:
        info = MONITORS.pop(url, None)
        if info:
            info["stop_event"].set()
    save_monitors()
    if info:
        print("🛑 Stopped monitoring:", url)
    else:
        print("⚠ I was not monitoring:", url)


def stop_all_monitors():
    with MONITOR_LOCK:
        count = len(MONITORS)
        for info in MONITORS.values():
            info["stop_event"].set()
        MONITORS.clear()
    save_monitors()
    if count:
        print(f"🛑 Stopped {count} website monitor(s).")


def list_monitors():
    with MONITOR_LOCK:
        if not MONITORS:
            print("No active website monitors.")
            return
        print()
        print("👁 ACTIVE WEBSITE MONITORS")
        print("-" * 70)
        for number, (url, info) in enumerate(MONITORS.items(), 1):
            status = info.get("last_status") or "waiting"
            checked = info.get("last_checked") or "not checked yet"
            print(f"{number}. {url}")
            print(f"   Status: {status}")
            print(f"   Interval: {info['interval']} seconds")
            print(f"   Last checked: {checked}")
            if info.get("last_change"):
                print(f"   Last change: {info['last_change']}")
        print("-" * 70)


def restore_monitors():
    saved = load_saved_monitors()
    if not saved:
        return
    print(f"🔄 Restoring {len(saved)} saved website monitor(s)...")
    for url, info in saved.items():
        try:
            interval = int(info.get("interval", 60))
        except Exception:
            interval = 60
        interval = max(15, interval)
        with MONITOR_LOCK:
            MONITORS[url] = {
                "url": url,
                "interval": interval,
                "fingerprint": None,
                "last_status": None,
                "last_checked": None,
                "last_change": info.get("last_change"),
                "stop_event": threading.Event()
            }
        threading.Thread(target=monitor_worker, args=(url,), daemon=True).start()


def parse_monitor_command(command):
    pattern = (
        r"^(?:can you |please )?"
        r"monitor(?: this)?(?: website| site)?\s+"
        r"(https?://\S+|www\.\S+|\S+)"
        r"(?:\s+every\s+(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m))?$"
    )
    match = re.match(pattern, command.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    url = normalize_url(match.group(1))
    amount = match.group(2)
    unit = match.group(3)
    interval = 60
    if amount:
        interval = int(amount)
        if unit.lower().startswith("m"):
            interval *= 60
    return url, max(15, interval)


def show_help():
    print()
    print("=" * 65)
    print("JARVIS V7.1 COMMANDS")
    print("=" * 65)
    print()
    print("OPEN / WEB")
    print("open website youtube.com")
    print("open website github.com")
    print("open app calculator")
    print("google search weather tomorrow")
    print("youtube search funny videos")
    print()
    print("FILES")
    print("search files homework")
    print(r"open path C:\Users\YourName\Desktop")
    print()
    print("SYSTEM")
    print("system info")
    print("defender status")
    print()
    print("MEMORY")
    print("remember that <fact>")
    print("show memory")
    print()
    print("WEBSITE MONITORING")
    print("monitor https://example.com")
    print("monitor https://example.com every 30 seconds")
    print("monitor https://example.com every 2 minutes")
    print("list monitors")
    print("stop monitoring https://example.com")
    print("stop all monitors")
    print()
    print("INSTAGRAM PUBLIC MONITORING")
    print("monitor instagram @_aan_yeaa_")
    print("monitor instagram @_aan_yeaa_ every 10 minutes")
    print("list instagram monitors")
    print("stop instagram @_aan_yeaa_")
    print("stop all instagram monitors")
    print()
    print("VOICE")
    print("voice")
    print()
    print("OTHER")
    print("help")
    print("exit")
    print()
    print("Local commands + monitoring work without")
    print("OpenRouter. General AI replies require an")
    print("AI provider.")
    print("=" * 65)
    print()


def voice_mode():
    print()
    print("🎙 VOICE MODE ACTIVE")
    print("Say 'exit voice' to return to typing.")
    print()
    while True:
        try:
            text = listen()
        except Exception as e:
            print("Voice error:", e)
            return
        if not text:
            continue
        print("You:", text)
        if text.lower().strip() in ("exit voice", "stop voice"):
            print("Voice mode stopped.")
            return
        if not try_local_command(text):
            ask_ai(text)


def ask_ai(command):
    if AI is None:
        print()
        print("🤖 General AI is currently OFF.")
        print("Local commands and website monitoring still work normally.")
        print("Type 'help' for commands.")
        print()
        return
    try:
        response = AI.ask(command)
        answer = response.content if hasattr(response, "content") else str(response)
        print()
        print("JARVIS:", answer)
        print()
    except Exception as e:
        print("AI error:", e)


def try_local_command(command):
    command = command.strip()
    lower = command.lower()
    if not command:
        return True
    if lower in ("exit", "quit", "shutdown", "goodbye"):
        raise KeyboardInterrupt
    if lower in ("help", "commands", "?"):
        show_help()
        return True
    if lower in ("voice", "voice mode"):
        voice_mode()
        return True

    # INSTAGRAM PUBLIC MONITORING
    if lower == "list instagram monitors":
        if list_instagram_monitors:
            list_instagram_monitors()
        else:
            print("Instagram monitoring feature is unavailable.")
        return True
    if lower == "stop all instagram monitors":
        if stop_all_instagram_monitors:
            stop_all_instagram_monitors()
        else:
            print("Instagram monitoring feature is unavailable.")
        return True
    if lower.startswith("stop instagram "):
        account = command[len("stop instagram "):].strip()
        if stop_instagram_monitor:
            stop_instagram_monitor(account)
        else:
            print("Instagram monitoring feature is unavailable.")
        return True
    if parse_instagram_monitor_command:
        instagram_command = parse_instagram_monitor_command(command)
        if instagram_command:
            account, interval = instagram_command
            if start_instagram_monitor:
                start_instagram_monitor(account, interval)
            else:
                print("Instagram monitoring feature is unavailable.")
            return True

    # WEBSITE MONITORING
    if lower == "list monitors":
        list_monitors()
        return True
    if lower == "stop all monitors":
        stop_all_monitors()
        return True
    if lower.startswith("stop monitoring "):
        url = command[len("stop monitoring "):].strip()
        stop_monitor(url)
        return True
    monitor_command = parse_monitor_command(command)
    if monitor_command:
        url, interval = monitor_command
        start_monitor(url, interval)
        return True

    # WEBSITES
    if lower.startswith("open website "):
        url = command[len("open website "):].strip()
        print(open_website(url))
        return True
    if lower.startswith("open http://") or lower.startswith("open https://"):
        url = command[len("open "):].strip()
        print(open_website(url))
        return True

    # APPS
    if lower.startswith("open app "):
        app = command[len("open app "):].strip()
        print(open_app(app))
        return True

    # GOOGLE
    if lower.startswith("google search "):
        query = command[len("google search "):].strip()
        print(web_search(query))
        return True
    if lower.startswith("search google for "):
        query = command[len("search google for "):].strip()
        print(web_search(query))
        return True

    # YOUTUBE
    if lower.startswith("youtube search "):
        query = command[len("youtube search "):].strip()
        print(youtube_search(query))
        return True
    if lower.startswith("search youtube for "):
        query = command[len("search youtube for "):].strip()
        print(youtube_search(query))
        return True

    # FILES
    if lower.startswith("search files "):
        query = command[len("search files "):].strip()
        print(search_files(query))
        return True
    if lower.startswith("open path "):
        path = command[len("open path "):].strip()
        print(open_path(path))
        return True

    # SYSTEM
    if lower in ("system info", "computer info", "pc info"):
        print(system_info())
        return True
    if lower in ("defender status", "windows defender", "security status"):
        print(defender_status())
        return True

    # MEMORY
    if lower.startswith("remember that "):
        fact = command[len("remember that "):].strip()
        if memory:
            try:
                memory.add(fact)
                print("🧠 Remembered.")
            except Exception as e:
                print("Memory error:", e)
        return True
    if lower.startswith("remember "):
        fact = command[len("remember "):].strip()
        if memory:
            try:
                memory.add(fact)
                print("🧠 Remembered.")
            except Exception as e:
                print("Memory error:", e)
        return True
    if lower in ("show memory", "memory", "what do you remember"):
        if memory:
            try:
                print(memory.show())
            except Exception as e:
                print("Memory error:", e)
        return True
    return False


def banner():
    ai_status = "ONLINE" if AI else "OFF"
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                    J A R V I S                         ║")
    print("║                      V 7.1                              ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║ Local commands: ONLINE                                  ║")
    print("║ Website monitoring: ONLINE                              ║")
    print("║ Instagram monitoring: ONLINE                            ║")
    print(f"║ AI provider: {ai_status:<43}║")
    print("║ Voice system: READY                                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def main():
    if check_and_apply_updates:
        try:
            check_and_apply_updates()
        except Exception as e:
            print("JARVIS: Updater error:", e)
    setup()
    banner()
    if requests is None:
        print("⚠ requests is not installed.")
        print("Website and Instagram monitoring need:")
        print("python -m pip install requests")
        print()
    restore_monitors()
    if restore_instagram_monitors:
        restore_instagram_monitors()
    print("Type 'help' for commands.")
    print("Type 'exit' to shut JARVIS down.")
    print()
    try:
        while True:
            try:
                command = input("You > ").strip()
                if not command:
                    continue
                handled = try_local_command(command)
                if not handled:
                    ask_ai(command)
            except EOFError:
                break
            except KeyboardInterrupt:
                print()
                print("🛑 Shutting down JARVIS...")
                break
            except Exception as e:
                print("Command error:", e)
    finally:
        stop_all_monitors()
        if stop_all_instagram_monitors:
            stop_all_instagram_monitors()
        if automation:
            try:
                automation.stop()
            except Exception:
                pass
        print("JARVIS offline. Goodbye.")


if __name__ == "__main__":
    main()
