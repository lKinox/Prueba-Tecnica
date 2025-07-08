import os
import json
import tempfile
import pytest

from app.main import app
from app.storage import ALERTS_FILE

@pytest.fixture
def client():
    return app.test_client()

@pytest.fixture(autouse=True)
def temp_alerts_file(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    monkeypatch.setattr("app.storage.ALERTS_FILE", path)
    data = [
        {
            "id": "alert-010",
            "title": "Test alert",
            "description": "Desc",
            "severity": "critical",
            "status": "active",
            "source_system": "test-system",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "assigned_to": None,
            "tags": ["test"]
        }
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    yield
    os.remove(path)

def test_create_alert(client):
    client = app.test_client()
    data = {
        "title": "New Alert",
        "description": "Description of the alert",
        "severity": "low",
        "source_system": "test-system",
        "assigned_to": None,
        "tags": []
    }
    res = client.post("/api/alerts", json=data)
    assert res.status_code == 201
    alert = res.get_json()
    assert alert["title"] == "New Alert"
    assert alert["status"] == "active"
    assert alert["id"]

def test_invalid_severity(client):
    client = app.test_client()
    data = {
        "title": "Invalid Alert",
        "description": "Desc",
        "severity": "super-high",
        "source_system": "test-system",
        "assigned_to": None,
        "tags": []
    }
    res = client.post("/api/alerts", json=data)
    assert res.status_code == 400
    assert "severity" in res.get_json()["error"]

def test_filter_by_severity(client):
    client = app.test_client()
    res = client.get("/api/alerts?severity=critical")
    assert res.status_code == 200
    data = res.get_json()
    assert data["meta"]["total"] == 1
    assert data["alerts"][0]["severity"] == "critical"