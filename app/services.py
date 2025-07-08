import uuid
from datetime import datetime
from copy import deepcopy

from .storage import load_alerts, save_alerts
from .models import SEVERITIES, STATUSES

def now_utc():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def get_alerts(filters=None, page=1, limit=10):
    alerts = load_alerts()
    filtered = []
    if filters:
        for alert in alerts:
            match = True
            for key, val in filters.items():
                if val and alert.get(key) != val:
                    match = False
                    break
            if match:
                filtered.append(alert)
    else:
        filtered = alerts

    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit
    paged = filtered[start:end]
    return paged, {"total": total, "page": page, "limit": limit}

def get_alert(alert_id):
    alerts = load_alerts()
    for alert in alerts:
        if alert["id"] == alert_id:
            return alert
    return None

def create_alert(data):
    alerts = load_alerts()
    alert = deepcopy(data)
    alert_id_num = next_alert_id(alerts)
    alert["id"] = f"alert-{alert_id_num:03d}"
    alert["created_at"] = now_utc()
    alert["updated_at"] = alert["created_at"]
    alert["status"] = "active"
    alerts.append(alert)
    save_alerts(alerts)
    return alert

def update_alert(alert_id, data):
    alerts = load_alerts()
    for i, alert in enumerate(alerts):
        if alert["id"] == alert_id:
            for key in data:
                if key in alert and key != "id":
                    alert[key] = data[key]
            alert["updated_at"] = now_utc()
            alerts[i] = alert
            save_alerts(alerts)
            return alert
    return None

def delete_alert(alert_id):
    alerts = load_alerts()
    new_alerts = [a for a in alerts if a["id"] != alert_id]
    if len(new_alerts) == len(alerts):
        return False
    save_alerts(new_alerts)
    return True

def acknowledge_alert(alert_id, assigned_to=None):
    alerts = load_alerts()
    for i, alert in enumerate(alerts):
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            alert["updated_at"] = now_utc()
            if assigned_to:
                alert["assigned_to"] = assigned_to
            alerts[i] = alert
            save_alerts(alerts)
            return alert
    return None

import re

def next_alert_id(alerts):
    nums = []
    for a in alerts:
        m = re.match(r"alert-(\d+)", a.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    return max(nums, default=0) + 1

def import_alerts(batch):
    import re
    external_ids = set()
    alerts = load_alerts()
    for alert in alerts:
        ext_id = alert.get("external_id")
        if ext_id:
            external_ids.add(ext_id)
    imported = []
    idx = next_alert_id(alerts)
    for raw in batch["alerts"]:
        if raw["external_id"] in external_ids:
            continue
        alert_id = f"alert-{idx:03d}"
        alert = {
            "id": alert_id,
            "title": raw["title"],
            "description": raw["description"],
            "severity": raw["severity"],
            "status": "active",
            "source_system": batch["source_system"],
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "assigned_to": None,
            "tags": [],
            "external_id": raw["external_id"]
        }
        alerts.append(alert)
        imported.append(alert)
        idx += 1
    save_alerts(alerts)
    return imported

def get_stats():
    alerts = load_alerts()
    by_severity = {sev: 0 for sev in SEVERITIES}
    by_status = {st: 0 for st in STATUSES}
    system_count = {}
    for alert in alerts:
        by_severity[alert["severity"]] += 1
        by_status[alert["status"]] += 1
        sys = alert["source_system"]
        system_count[sys] = system_count.get(sys, 0) + 1
    top_system = max(system_count, key=system_count.get) if system_count else None
    return {
        "by_severity": by_severity,
        "by_status": by_status,
        "system_with_most_alerts": top_system
    }