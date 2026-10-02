"""
Unit tests for Live OpenStack stack telemetry and Apache Guacamole monitoring endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app
from src.db.database import SessionLocal
from src.db.models import User, ApiKey
from src.db.security import hash_password, generate_api_key


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(username="admin", hashed_password=hash_password("admin"), role="admin", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    client = TestClient(app)
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    token = res.json()["access_token"]
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_openstack_stacks_unauthenticated(client):
    res = client.get("/api/live/openstack/stacks")
    assert res.status_code == 401


def test_openstack_stacks_authenticated(client, auth_headers):
    res = client.get("/api/live/openstack/stacks", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "stacks" in data
    assert "count" in data
    assert isinstance(data["stacks"], list)
    assert len(data["stacks"]) > 0
    first = data["stacks"][0]
    assert "status" in first
    assert "name" in first


def test_openstack_stack_resources(client, auth_headers):
    res = client.get("/api/live/openstack/stacks/cyberrange-stack-01/resources", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "resources" in data
    assert len(data["resources"]) > 0
    assert any("OS::Nova::Server" in r["type"] for r in data["resources"])


def test_guacamole_monitoring(client, auth_headers):
    res = client.get("/api/live/guacamole/monitoring", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_sessions" in data
    assert "history" in data
    assert "connections" in data
    assert isinstance(data["active_sessions"], list)


def test_guacamole_terminate_session(client, auth_headers):
    res = client.delete("/api/live/guacamole/active-connections/session-test-id", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "message" in data


def test_api_key_access_to_live_monitoring(client):
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    full_key, prefix, key_hash = generate_api_key()
    api_key_record = ApiKey(
        user_id=admin.id,
        name="Telemetry Pipeline Key",
        prefix=prefix,
        key_hash=key_hash,
        is_active=True
    )
    db.add(api_key_record)
    db.commit()

    res = client.get("/api/live/openstack/stacks", headers={"X-API-Key": full_key})
    assert res.status_code == 200
    db.delete(api_key_record)
    db.commit()
    db.close()

