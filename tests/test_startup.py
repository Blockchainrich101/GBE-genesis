import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

def test_complete_request_persists_across_restart(tmp_path):
    path = tmp_path / "requests.sqlite3"
    with TestClient(create_app(path)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/health/live").json()["status"] == "alive"
        assert client.get("/health/ready").json()["ai_enabled"] is False
        response = client.post("/api/requests", json={"action":"diagnose","text":"Check startup"})
        assert response.status_code == 200
        request_id = response.json()["id"]
    with TestClient(create_app(path)) as client:
        assert client.get("/health/ready").status_code == 200
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT description FROM requests WHERE id=?", (request_id,)).fetchone() == ("Check startup",)

@pytest.mark.parametrize("payload", [
    {"action":"send_email","text":"hello"},
    {"action":"diagnose","text":"   "},
    {"action":"diagnose","text":"x"*4001},
    {},
])
def test_reject_invalid_request(tmp_path, payload):
    with TestClient(create_app(tmp_path / "db")) as client:
        assert client.post("/api/requests", json=payload).status_code == 422

def test_invalid_storage_fails_startup(tmp_path):
    with pytest.raises(RuntimeError, match="Database startup failed"):
        with TestClient(create_app(tmp_path)):
            pass

def test_runtime_storage_failure_is_visible(tmp_path):
    path = tmp_path / "db"
    with TestClient(create_app(path)) as client:
        with sqlite3.connect(path) as db:
            db.execute("DROP TABLE requests")
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        response = client.post("/api/requests", json={"action":"diagnose","text":"hello"})
        assert response.status_code == 503
        assert "Could not save" in response.json()["detail"]
