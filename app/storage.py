import json
import threading

ALERTS_FILE = "data/alerts.json"
LOCK = threading.Lock()

def load_alerts():
    with LOCK:
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

def save_alerts(alerts):
    with LOCK:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2)