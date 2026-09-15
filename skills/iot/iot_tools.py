import json
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
SENSOR_FILE = DATA / "sensor_readings.json"


def save_sensor_reading(data):
    readings = []
    if SENSOR_FILE.exists():
        try:
            readings = json.loads(SENSOR_FILE.read_text(encoding="utf-8"))
        except Exception:
            readings = []
    readings.append(data)
    readings = readings[-500:]
    SENSOR_FILE.write_text(json.dumps(readings, indent=2), encoding="utf-8")
    return "Sensor reading saved locally."


def latest_sensor():
    if not SENSOR_FILE.exists():
        return "No sensor readings stored yet."
    try:
        data = json.loads(SENSOR_FILE.read_text(encoding="utf-8"))
        if not data:
            return "No sensor readings stored yet."
        return json.dumps(data[-1], indent=2)
    except Exception as exc:
        return f"Sensor database error: {exc}"


def weather_url(city):
    q = urllib.parse.quote_plus(city.strip())
    return f"https://wttr.in/{q}?format=j1"


def get_weather(city):
    try:
        req = urllib.request.Request(weather_url(city), headers={"User-Agent": "JARVIS/8"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        return f"{city}: {desc}, {current['temp_C']} C, humidity {current['humidity']}%, wind {current['windspeedKmph']} km/h."
    except Exception as exc:
        return f"Weather lookup failed: {exc}"
