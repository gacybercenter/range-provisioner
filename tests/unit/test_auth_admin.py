"""
Unit tests for Authentication, User Management, and Datasource endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app
from src.db import init_db
from src.db.database import SessionLocal
from src.db.models import User, OpenStackDataSource, GuacamoleDataSource, SavedRange


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert res.status_code == 401


def test_auth_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["authenticated"] is False


def test_auth_me_authenticated(client):
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    token = login_res.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["authenticated"] is True
    assert res.json()["user"]["username"] == "admin"


def test_admin_user_crud(client):
    # Login as admin
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    admin_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create operator user
    create_res = client.post(
        "/api/admin/users",
        json={"username": "test_operator", "password": "OperatorPass123!", "role": "operator"},
        headers=headers,
    )
    assert create_res.status_code == 200
    user_id = create_res.json()["user_id"]

    # 2. List users
    list_res = client.get("/api/admin/users", headers=headers)
    assert list_res.status_code == 200
    usernames = [u["username"] for u in list_res.json()]
    assert "test_operator" in usernames

    # 3. Test operator cannot access admin endpoints
    op_login = client.post("/api/auth/login", json={"username": "test_operator", "password": "OperatorPass123!"})
    op_token = op_login.json()["access_token"]
    op_headers = {"Authorization": f"Bearer {op_token}"}

    op_forbidden = client.get("/api/admin/users", headers=op_headers)
    assert op_forbidden.status_code == 403

    # 4. Update user
    update_res = client.put(f"/api/admin/users/{user_id}", json={"role": "viewer"}, headers=headers)
    assert update_res.status_code == 200

    # 5. Delete user
    del_res = client.delete(f"/api/admin/users/{user_id}", headers=headers)
    assert del_res.status_code == 200


def test_openstack_datasource_crud(client):
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Create OpenStack DS
    create_res = client.post(
        "/api/admin/datasources/openstack",
        json={
            "name": "lab-openstack",
            "auth_url": "http://192.168.10.5:5000/v3",
            "username": "openstack_admin",
            "password": "OpenStackSecurePass!",
            "project_name": "range_dev",
            "user_domain_name": "Default",
            "project_domain_name": "Default",
            "is_default": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    ds_id = create_res.json()["id"]

    # List OpenStack DS
    list_res = client.get("/api/admin/datasources/openstack", headers=headers)
    assert list_res.status_code == 200
    names = [ds["name"] for ds in list_res.json()]
    assert "lab-openstack" in names

    # Update OpenStack DS
    update_res = client.put(
        f"/api/admin/datasources/openstack/{ds_id}",
        json={"name": "lab-openstack-renamed", "project_name": "range_prod"},
        headers=headers,
    )
    assert update_res.status_code == 200

    list_res2 = client.get("/api/admin/datasources/openstack", headers=headers)
    assert any(ds["name"] == "lab-openstack-renamed" for ds in list_res2.json())

    # Delete OpenStack DS
    del_res = client.delete(f"/api/admin/datasources/openstack/{ds_id}", headers=headers)
    assert del_res.status_code == 200


def test_guacamole_datasource_crud(client):
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Create Guacamole DS
    create_res = client.post(
        "/api/admin/datasources/guacamole",
        json={
            "name": "lab-guacamole",
            "host": "http://192.168.10.20:8080/guacamole",
            "data_source": "mysql",
            "username": "guacadmin",
            "password": "GuacAdminPassword!",
            "is_default": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    ds_id = create_res.json()["id"]

    # List Guacamole DS
    list_res = client.get("/api/admin/datasources/guacamole", headers=headers)
    assert list_res.status_code == 200
    names = [ds["name"] for ds in list_res.json()]
    assert "lab-guacamole" in names

    # Update Guacamole DS
    update_res = client.put(
        f"/api/admin/datasources/guacamole/{ds_id}",
        json={"name": "lab-guacamole-renamed", "data_source": "postgresql"},
        headers=headers,
    )
    assert update_res.status_code == 200

    list_res2 = client.get("/api/admin/datasources/guacamole", headers=headers)
    assert any(ds["name"] == "lab-guacamole-renamed" and ds["data_source"] == "postgresql" for ds in list_res2.json())

    # Delete Guacamole DS
    del_res = client.delete(f"/api/admin/datasources/guacamole/{ds_id}", headers=headers)
    assert del_res.status_code == 200


def test_saved_range_crud(client):
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Save a range
    save_res = client.post(
        "/api/ranges",
        json={
            "name": "Test Blue Team Range",
            "organization": "blueteam",
            "description": "SOC training environment with Kali and SIEM",
            "stack_count": 2,
            "globals_yaml": "globals:\n  org: blueteam\n",
            "heat_yaml": "heat_template_version: 2018-03-02\n",
            "guac_yaml": "groups:\n  blueteam: {}\n",
        },
        headers=headers,
    )
    assert save_res.status_code == 200
    range_id = save_res.json()["id"]

    # List saved ranges
    list_res = client.get("/api/ranges")
    assert list_res.status_code == 200
    names = [r["name"] for r in list_res.json()]
    assert "Test Blue Team Range" in names

    # Get single range details
    get_res = client.get(f"/api/ranges/{range_id}")
    assert get_res.status_code == 200
    assert get_res.json()["organization"] == "blueteam"

    # Delete saved range
    del_res = client.delete(f"/api/ranges/{range_id}", headers=headers)
    assert del_res.status_code == 200
