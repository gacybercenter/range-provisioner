"""
Authentication and admin management routes for Users, OpenStack, and Guacamole datasources.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from src.db.database import get_db
    from src.db.models import User, OpenStackDataSource, GuacamoleDataSource, SavedRange, ApiKey, SystemSetting
    from src.db.security import (
        hash_password,
        verify_password,
        create_access_token,
        generate_api_key,
        get_current_user,
        require_user,
        require_admin,
    )
    from src.utils import connections as conn_utils
    from src.config.heat_parser import HeatTemplateParser, build_range_topology
except ImportError:
    from db.database import get_db
    from db.models import User, OpenStackDataSource, GuacamoleDataSource, SavedRange, ApiKey, SystemSetting
    from db.security import (
        hash_password,
        verify_password,
        create_access_token,
        generate_api_key,
        get_current_user,
        require_user,
        require_admin,
    )
    from utils import connections as conn_utils
    from config.heat_parser import HeatTemplateParser, build_range_topology


router = APIRouter(prefix="/api")


# --- Auth Schemas ---
class LoginPayload(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime


class UserCreatePayload(BaseModel):
    username: str
    password: str
    role: str = Field(default="operator")  # 'admin', 'operator', 'viewer'


class UserUpdatePayload(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# --- Datasource Schemas ---
class OpenStackCreatePayload(BaseModel):
    name: str
    auth_url: str
    username: str
    password: str
    project_name: str
    user_domain_name: str = "Default"
    project_domain_name: str = "Default"
    region_name: Optional[str] = None
    is_default: bool = False


class OpenStackUpdatePayload(BaseModel):
    name: Optional[str] = None
    auth_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    project_name: Optional[str] = None
    user_domain_name: Optional[str] = None
    project_domain_name: Optional[str] = None
    region_name: Optional[str] = None
    is_default: Optional[bool] = None


class OpenStackResponse(BaseModel):
    id: int
    name: str
    auth_url: str
    username: str
    project_name: str
    user_domain_name: str
    project_domain_name: str
    region_name: Optional[str]
    is_default: bool
    created_at: datetime


class GuacamoleCreatePayload(BaseModel):
    name: str
    host: str
    data_source: str = "mysql"
    username: str
    password: str
    is_default: bool = False


class GuacamoleUpdatePayload(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    data_source: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_default: Optional[bool] = None


class GuacamoleResponse(BaseModel):
    id: int
    name: str
    host: str
    data_source: str
    username: str
    is_default: bool
    created_at: datetime



# =========================================================================
# Authentication Endpoints
# =========================================================================

@router.post("/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """Authenticate with username and password, returns JWT token."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    }


@router.get("/auth/me")
def get_current_user_profile(user: Optional[User] = Depends(get_current_user)):
    """Get profile of current logged in user."""
    if not user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    }


# =========================================================================
# Admin: User Management Endpoints
# =========================================================================

@router.get("/admin/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all user accounts (Admin only)."""
    users = db.query(User).order_by(User.id).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/admin/users")
def create_user(payload: UserCreatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new user account (Admin only)."""
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "user_id": new_user.id}


@router.put("/admin/users/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Update a user account role, active status, or password (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        # Prevent disabling the current admin
        if user.id == admin.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="Cannot disable your own admin account")
        user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    return {"message": "User updated"}


@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Delete a user account (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# =========================================================================
# Admin: OpenStack Data Source Management
# =========================================================================

@router.get("/admin/datasources/openstack")
def list_openstack_datasources(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List OpenStack data sources (Admin only)."""
    items = db.query(OpenStackDataSource).all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "auth_url": i.auth_url,
            "username": i.username,
            "project_name": i.project_name,
            "user_domain_name": i.user_domain_name,
            "project_domain_name": i.project_domain_name,
            "region_name": i.region_name,
            "is_default": i.is_default,
        }
        for i in items
    ]


@router.post("/admin/datasources/openstack")
def create_openstack_datasource(payload: OpenStackCreatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Add a new OpenStack data source (Admin only)."""
    if payload.is_default:
        db.query(OpenStackDataSource).update({"is_default": False})

    ds = OpenStackDataSource(
        name=payload.name,
        auth_url=payload.auth_url,
        username=payload.username,
        password=payload.password,
        project_name=payload.project_name,
        user_domain_name=payload.user_domain_name,
        project_domain_name=payload.project_domain_name,
        region_name=payload.region_name,
        is_default=payload.is_default,
    )
    db.add(ds)
    db.commit()
    return {"message": "OpenStack datasource created", "id": ds.id}


@router.delete("/admin/datasources/openstack/{ds_id}")
def delete_openstack_datasource(ds_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Delete an OpenStack data source (Admin only)."""
    ds = db.query(OpenStackDataSource).filter(OpenStackDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    db.delete(ds)
    db.commit()
    return {"message": "OpenStack datasource deleted"}


@router.put("/admin/datasources/openstack/{ds_id}")
def update_openstack_datasource(ds_id: int, payload: OpenStackUpdatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Update an OpenStack data source (Admin only)."""
    ds = db.query(OpenStackDataSource).filter(OpenStackDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    if payload.is_default:
        db.query(OpenStackDataSource).filter(OpenStackDataSource.id != ds_id).update({"is_default": False})

    if payload.name is not None:
        ds.name = payload.name
    if payload.auth_url is not None:
        ds.auth_url = payload.auth_url
    if payload.username is not None:
        ds.username = payload.username
    if payload.password:
        ds.password = payload.password
    if payload.project_name is not None:
        ds.project_name = payload.project_name
    if payload.user_domain_name is not None:
        ds.user_domain_name = payload.user_domain_name
    if payload.project_domain_name is not None:
        ds.project_domain_name = payload.project_domain_name
    if payload.region_name is not None:
        ds.region_name = payload.region_name
    if payload.is_default is not None:
        ds.is_default = payload.is_default

    db.commit()
    return {"message": "OpenStack datasource updated"}



@router.post("/admin/datasources/openstack/{ds_id}/test")
def test_openstack_datasource(ds_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Test connection to OpenStack data source."""
    ds = db.query(OpenStackDataSource).filter(OpenStackDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    cloud_dict = ds.to_clouds_dict()
    try:
        conn = conn_utils.openstack_connection(ds.name, cloud_dict, debug=True)
        if conn:
            return {"success": True, "message": "Successfully connected to OpenStack!"}
        return {"success": False, "message": "Connection returned None"}
    except Exception as exc:
        return {"success": False, "message": f"Connection failed: {str(exc)}"}


# =========================================================================
# Admin: Guacamole Data Source Management
# =========================================================================

@router.get("/admin/datasources/guacamole")
def list_guacamole_datasources(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List Guacamole data sources (Admin only)."""
    items = db.query(GuacamoleDataSource).all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "host": i.host,
            "data_source": i.data_source,
            "username": i.username,
            "is_default": i.is_default,
        }
        for i in items
    ]


@router.post("/admin/datasources/guacamole")
def create_guacamole_datasource(payload: GuacamoleCreatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Add a new Guacamole data source (Admin only)."""
    if payload.is_default:
        db.query(GuacamoleDataSource).update({"is_default": False})

    ds = GuacamoleDataSource(
        name=payload.name,
        host=payload.host,
        data_source=payload.data_source,
        username=payload.username,
        password=payload.password,
        is_default=payload.is_default,
    )
    db.add(ds)
    db.commit()
    return {"message": "Guacamole datasource created", "id": ds.id}


@router.delete("/admin/datasources/guacamole/{ds_id}")
def delete_guacamole_datasource(ds_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Delete a Guacamole data source (Admin only)."""
    ds = db.query(GuacamoleDataSource).filter(GuacamoleDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    db.delete(ds)
    db.commit()
    return {"message": "Guacamole datasource deleted"}


@router.put("/admin/datasources/guacamole/{ds_id}")
def update_guacamole_datasource(ds_id: int, payload: GuacamoleUpdatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Update a Guacamole data source (Admin only)."""
    ds = db.query(GuacamoleDataSource).filter(GuacamoleDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    if payload.is_default:
        db.query(GuacamoleDataSource).filter(GuacamoleDataSource.id != ds_id).update({"is_default": False})

    if payload.name is not None:
        ds.name = payload.name
    if payload.host is not None:
        ds.host = payload.host
    if payload.data_source is not None:
        ds.data_source = payload.data_source
    if payload.username is not None:
        ds.username = payload.username
    if payload.password:
        ds.password = payload.password
    if payload.is_default is not None:
        ds.is_default = payload.is_default

    db.commit()
    return {"message": "Guacamole datasource updated"}



@router.post("/admin/datasources/guacamole/{ds_id}/test")
def test_guacamole_datasource(ds_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Test connection to Guacamole data source."""
    ds = db.query(GuacamoleDataSource).filter(GuacamoleDataSource.id == ds_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    cloud_dict = ds.to_clouds_dict()
    try:
        conn = conn_utils.guacamole_connection(ds.name, cloud_dict, debug=True)
        if conn:
            return {"success": True, "message": "Successfully connected to Guacamole!"}
        return {"success": False, "message": "Connection returned None"}
    except Exception as exc:
        return {"success": False, "message": f"Connection failed: {str(exc)}"}


# =========================================================================
# Saved Range Endpoints (SQLite DB Storage)
# =========================================================================

class SavedRangePayload(BaseModel):
    name: str
    organization: str
    description: Optional[str] = None
    stack_count: int = 1
    users_per_system: int = 2
    protocol: str = "rdp"
    port: int = 3389
    student_user: str = "student"
    student_pass: str = "RangeP@ss123!"
    enable_swift: bool = False
    heat_yaml: str
    globals_yaml: Optional[str] = None
    guac_yaml: Optional[str] = None
    config_json: Optional[str] = None


class HeatValidateRequest(BaseModel):
    heat_yaml: str


class TopologyRequest(BaseModel):
    heat_yaml: str
    stack_count: int = 1
    organization: str = "cyberrange"
    protocol: str = "rdp"
    port: int = 3389
    student_user: str = "student"
    users_per_system: int = 2
    enable_swift: bool = False


@router.post("/heat/validate")
def validate_heat_hot_template(payload: HeatValidateRequest):
    """Validate OpenStack HOT template syntax, resource schema, parameter references, and dependency loops."""
    parser = HeatTemplateParser(payload.heat_yaml)
    result = parser.parse()
    return result.to_dict()


@router.post("/topology")
def generate_topology(payload: TopologyRequest):
    """Generate interactive D3 graph topology from range configuration."""
    return build_range_topology(
        hot_template=payload.heat_yaml,
        stack_count=payload.stack_count,
        organization=payload.organization,
        protocol=payload.protocol,
        port=payload.port,
        student_user=payload.student_user,
        users_per_system=payload.users_per_system,
        enable_swift=payload.enable_swift,
    )


@router.get("/ranges")
def list_saved_ranges(db: Session = Depends(get_db)):
    """List all saved cyber ranges stored in SQLite."""
    ranges = db.query(SavedRange).order_by(SavedRange.updated_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "organization": r.organization,
            "description": r.description,
            "stack_count": r.stack_count,
            "users_per_system": r.users_per_system,
            "protocol": r.protocol,
            "port": r.port,
            "student_user": r.student_user,
            "enable_swift": r.enable_swift,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        }
        for r in ranges
    ]


@router.get("/ranges/{range_id}")
def get_saved_range(range_id: int, db: Session = Depends(get_db)):
    """Get complete configuration of a saved cyber range from SQLite."""
    r = db.query(SavedRange).filter(SavedRange.id == range_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Saved range not found")
    return {
        "id": r.id,
        "name": r.name,
        "organization": r.organization,
        "description": r.description,
        "stack_count": r.stack_count,
        "users_per_system": r.users_per_system,
        "protocol": r.protocol,
        "port": r.port,
        "student_user": r.student_user,
        "student_pass": r.student_pass,
        "enable_swift": r.enable_swift,
        "heat_yaml": r.heat_yaml,
        "globals_yaml": r.globals_yaml,
        "guac_yaml": r.guac_yaml,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


@router.get("/ranges/{range_id}/topology")
def get_saved_range_topology(range_id: int, db: Session = Depends(get_db)):
    """Generate D3 topology graph for a saved cyber range."""
    r = db.query(SavedRange).filter(SavedRange.id == range_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Saved range not found")
    return build_range_topology(
        hot_template=r.heat_yaml,
        stack_count=r.stack_count,
        organization=r.organization,
        protocol=r.protocol,
        port=r.port,
        student_user=r.student_user,
        users_per_system=r.users_per_system,
        enable_swift=r.enable_swift,
    )


@router.post("/ranges")
def save_range(payload: SavedRangePayload, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Save or update a range configuration in SQLite DB without templates on disk."""
    existing = db.query(SavedRange).filter(SavedRange.name == payload.name).first()
    if existing:
        existing.organization = payload.organization
        existing.description = payload.description
        existing.stack_count = payload.stack_count
        existing.users_per_system = payload.users_per_system
        existing.protocol = payload.protocol
        existing.port = payload.port
        existing.student_user = payload.student_user
        existing.student_pass = payload.student_pass
        existing.enable_swift = payload.enable_swift
        existing.heat_yaml = payload.heat_yaml
        existing.globals_yaml = payload.globals_yaml
        existing.guac_yaml = payload.guac_yaml
        existing.config_json = payload.config_json
        db.commit()
        return {"message": "Saved range updated", "id": existing.id}

    r = SavedRange(
        name=payload.name,
        organization=payload.organization,
        description=payload.description,
        stack_count=payload.stack_count,
        users_per_system=payload.users_per_system,
        protocol=payload.protocol,
        port=payload.port,
        student_user=payload.student_user,
        student_pass=payload.student_pass,
        enable_swift=payload.enable_swift,
        heat_yaml=payload.heat_yaml,
        globals_yaml=payload.globals_yaml,
        guac_yaml=payload.guac_yaml,
        config_json=payload.config_json,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"message": "Range saved successfully", "id": r.id}


@router.delete("/ranges/{range_id}")
def delete_saved_range(range_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Delete a saved range configuration from SQLite."""
    r = db.query(SavedRange).filter(SavedRange.id == range_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Saved range not found")
    db.delete(r)
    db.commit()
    return {"message": "Saved range deleted"}


# =========================================================================
# API Key Management Endpoints
# =========================================================================

class ApiKeyCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    user_id: Optional[int] = None


@router.get("/admin/api-keys")
def list_api_keys(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all API keys (Admin only)."""
    keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.prefix,
            "user_id": k.user_id,
            "username": k.user.username if k.user else "Unknown",
            "is_active": k.is_active,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
        }
        for k in keys
    ]


@router.post("/admin/api-keys")
def create_api_key_endpoint(payload: ApiKeyCreatePayload, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create a new API key. Returns the raw secret key once."""
    target_user_id = payload.user_id or admin.id
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    full_key, key_prefix, key_hash = generate_api_key()
    new_key = ApiKey(
        user_id=target_user_id,
        name=payload.name,
        prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return {
        "message": "API key created successfully. Save it now, as it cannot be retrieved again.",
        "id": new_key.id,
        "name": new_key.name,
        "prefix": new_key.prefix,
        "api_key": full_key,
    }


@router.delete("/admin/api-keys/{key_id}")
def delete_api_key_endpoint(key_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Revoke and delete an API key."""
    key_obj = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key_obj)
    db.commit()
    return {"message": "API key deleted"}


# =========================================================================
# Global System Settings Endpoints
# =========================================================================

class SettingsBatchUpdate(BaseModel):
    settings: dict


@router.get("/admin/settings")
def get_system_settings(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get all global system settings categorized."""
    all_settings = db.query(SystemSetting).all()
    grouped = {}
    flat = {}
    for s in all_settings:
        if s.category not in grouped:
            grouped[s.category] = []
        grouped[s.category].append({
            "key": s.key,
            "value": s.value,
            "category": s.category,
            "description": s.description,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
        flat[s.key] = s.value

    return {
        "grouped": grouped,
        "flat": flat,
    }


@router.put("/admin/settings")
def update_system_settings(payload: SettingsBatchUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Update one or more global system settings."""
    for key, val in payload.settings.items():
        val_str = str(val).lower() if isinstance(val, bool) else str(val)
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if existing:
            existing.value = val_str
        else:
            db.add(SystemSetting(key=key, value=val_str, category="custom"))
    db.commit()
    return {"message": "Settings updated successfully"}


@router.post("/admin/maintenance/vacuum")
def vacuum_database(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Optimize and vacuum SQLite database."""
    import os
    from sqlalchemy import text
    try:
        db.execute(text("VACUUM;"))
        db.commit()
        db_path = "range_provisioner.db"
        size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        size_kb = round(size_bytes / 1024, 2)
        return {"success": True, "message": f"Database optimized. Current size: {size_kb} KB"}
    except Exception as e:
        return {"success": False, "message": f"Vacuum failed: {str(e)}"}


@router.post("/admin/maintenance/test-webhook")
def test_webhook(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Send test alert to configured webhook URL."""
    import urllib.request
    import json
    wh = db.query(SystemSetting).filter(SystemSetting.key == "webhook_url").first()
    if not wh or not wh.value.strip():
        raise HTTPException(status_code=400, detail="Webhook URL is not configured")

    try:
        test_payload = {
            "event": "test_alert",
            "message": "Range Provisioner Webhook Test",
            "timestamp": datetime.now().isoformat(),
            "sender": admin.username,
        }
        data = json.dumps(test_payload).encode("utf-8")
        req = urllib.request.Request(
            wh.value.strip(),
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "RangeProvisioner/2.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            return {"success": True, "message": f"Webhook test sent successfully (HTTP {status_code})"}
    except Exception as e:
        return {"success": False, "message": f"Webhook delivery error: {str(e)}"}



