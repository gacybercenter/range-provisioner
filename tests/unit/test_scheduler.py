"""
Unit tests for Scheduled Provisioning & Deprovisioning (API, Engine, DB, Background Poller).
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.web.app import app
from src.db import init_db
from src.db.database import SessionLocal
from src.db.models import ScheduledJob
from src.web.routes.scheduler import check_pending_schedules, execute_schedule_action_sync


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_schedules_require_auth(client):
    res = client.get("/api/schedules")
    assert res.status_code == 401


def test_create_schedule_validation_errors(client, auth_headers):
    # Missing both build_at and delete_at
    res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={"name": "Empty Schedule", "target": "full"}
    )
    assert res.status_code == 400
    assert "At least one of build_at or delete_at" in res.json()["detail"]

    # Invalid target
    res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={
            "name": "Invalid Target",
            "target": "unsupported",
            "build_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
    )
    assert res.status_code == 400
    assert "Invalid target" in res.json()["detail"]


def test_create_and_get_schedule(client, auth_headers):
    build_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    delete_time = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()

    create_res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={
            "name": "Exercise Alpha Automated Lifecycle",
            "target": "full",
            "dry_run": True,
            "build_at": build_time,
            "delete_at": delete_time
        }
    )
    assert create_res.status_code == 200
    data = create_res.json()
    job_id = data["id"]
    assert data["name"] == "Exercise Alpha Automated Lifecycle"
    assert data["build_status"] == "scheduled"
    assert data["delete_status"] == "scheduled"
    assert data["dry_run"] is True

    # Retrieve schedule by ID
    get_res = client.get(f"/api/schedules/{job_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # List schedules
    list_res = client.get("/api/schedules", headers=auth_headers)
    assert list_res.status_code == 200
    ids = [item["id"] for item in list_res.json()]
    assert job_id in ids


def test_cancel_schedule_actions(client, auth_headers):
    build_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    delete_time = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()

    create_res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={
            "name": "Cancellable Exercise",
            "target": "openstack",
            "dry_run": True,
            "build_at": build_time,
            "delete_at": delete_time
        }
    )
    job_id = create_res.json()["id"]

    # Cancel build
    cancel_build = client.post(f"/api/schedules/{job_id}/cancel-build", headers=auth_headers)
    assert cancel_build.status_code == 200
    assert cancel_build.json()["build_status"] == "cancelled"

    # Cancel delete
    cancel_del = client.post(f"/api/schedules/{job_id}/cancel-delete", headers=auth_headers)
    assert cancel_del.status_code == 200
    assert cancel_del.json()["delete_status"] == "cancelled"


def test_trigger_schedule_action_now(client, auth_headers):
    create_res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={
            "name": "Immediate Trigger Test",
            "target": "full",
            "dry_run": True,
            "build_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
    )
    job_id = create_res.json()["id"]

    with patch("src.web.routes.scheduler.execute_schedule_action_sync") as mock_exec:
        trigger_res = client.post(f"/api/schedules/{job_id}/trigger-build", headers=auth_headers)
        assert trigger_res.status_code == 200
        assert trigger_res.json()["build_status"] == "in_progress"
        # Background worker called
        mock_exec.assert_called_once_with(job_id, "create")


def test_update_and_delete_schedule(client, auth_headers):
    create_res = client.post(
        "/api/schedules",
        headers=auth_headers,
        json={
            "name": "To Be Deleted",
            "target": "guacamole",
            "dry_run": True,
            "build_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        }
    )
    job_id = create_res.json()["id"]

    # Update
    update_res = client.put(
        f"/api/schedules/{job_id}",
        headers=auth_headers,
        json={"name": "Renamed Schedule", "dry_run": False}
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Renamed Schedule"
    assert update_res.json()["dry_run"] is False

    # Delete
    del_res = client.delete(f"/api/schedules/{job_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Verify not found
    get_res = client.get(f"/api/schedules/{job_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_check_pending_schedules_worker():
    db = SessionLocal()
    try:
        # Create a job with build_at 10 minutes in the past
        past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
        job = ScheduledJob(
            name="Past Due Job",
            target="full",
            dry_run=True,
            build_at=past_time,
            build_status="scheduled",
            delete_status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        with patch("src.web.routes.scheduler.execute_schedule_action_sync") as mock_exec:
            check_pending_schedules()
            mock_exec.assert_called_with(job_id, "create")

            db.refresh(job)
            assert job.build_status == "in_progress"

        # Cleanup
        db.delete(job)
        db.commit()
    finally:
        db.close()


def test_execute_schedule_action_dry_run_sync():
    db = SessionLocal()
    try:
        job = ScheduledJob(
            name="Dry Run Real Execution",
            target="full",
            dry_run=True,
            build_status="in_progress",
            delete_status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        # Execute build action
        execute_schedule_action_sync(job_id, "create")

        db.refresh(job)
        assert job.build_status == "completed"
        assert "Initiating Range Provisioner" in (job.build_log or "")
        assert "[DRY-RUN]" in (job.build_log or "")

        # Execute teardown action
        execute_schedule_action_sync(job_id, "delete")
        db.refresh(job)
        assert job.delete_status == "completed"
        assert "Initiating Range Provisioner" in (job.delete_log or "")

        # Cleanup
        db.delete(job)
        db.commit()
    finally:
        db.close()

