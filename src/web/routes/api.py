"""
REST API endpoints for Range Provisioner web interface.
"""
import io
import os
import zipfile
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

try:
    from src.config.validator import (
        validate_range_package,
        validate_globals,
        validate_heat_template,
        validate_guacamole_template,
    )
    from src.config.models import RangeConfig
    from src.utils import load_template
    from src.provision.engine import ProvisionEngine
    from src.utils.events import dispatcher, ProvisionEvent
except ImportError:
    from config.validator import (
        validate_range_package,
        validate_globals,
        validate_heat_template,
        validate_guacamole_template,
    )
    from config.models import RangeConfig
    from utils import load_template
    from provision.engine import ProvisionEngine
    from utils.events import dispatcher, ProvisionEvent

router = APIRouter(prefix="/api")

TASKS: Dict[str, Dict[str, Any]] = {}


class ValidatePayload(BaseModel):
    globals_yaml: str
    heat_yaml: Optional[str] = None
    guac_yaml: Optional[str] = None


class GeneratePayload(BaseModel):
    organization: str = Field(default="cyberrange", description="Organization name")
    stack_count: int = Field(default=2, ge=1, le=50, description="Number of Heat stacks")
    users_per_system: int = Field(default=2, ge=1, le=100, description="Number of users per system")
    protocol: str = Field(default="rdp", description="Default protocol (rdp, ssh, vnc)")
    port: int = Field(default=3389, description="Port")
    student_user: str = Field(default="student", description="VM login user")
    student_pass: str = Field(default="RangeP@ss123!", description="VM login password")
    enable_swift: bool = Field(default=False, description="Enable Swift storage")


class ProvisionPayload(BaseModel):
    target: str = Field(default="full", description="full, heat, guacamole, swift")
    action: str = Field(default="create", description="create, update, delete")
    dry_run: bool = Field(default=True, description="Dry-run simulation mode")
    range_id: Optional[int] = None
    organization: Optional[str] = "cyberrange"
    stack_count: Optional[int] = 1
    users_per_system: Optional[int] = 2
    protocol: Optional[str] = "rdp"
    port: Optional[int] = 3389
    student_user: Optional[str] = "student"
    student_pass: Optional[str] = "RangeP@ss123!"
    enable_swift: Optional[bool] = False
    globals_yaml: Optional[str] = None
    heat_yaml: Optional[str] = None
    guac_yaml: Optional[str] = None
    clouds_yaml: Optional[str] = None



@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "range-provisioner",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/config/validate")
def validate_configuration(payload: ValidatePayload):
    result = validate_range_package(
        globals_data=payload.globals_yaml,
        heat_data=payload.heat_yaml,
        guac_data=payload.guac_yaml,
    )
    return result.to_dict()


@router.post("/config/inspect")
def inspect_configuration(payload: ValidatePayload):
    g_valid, g_dict, g_err = False, {}, None
    try:
        g_dict = load_template.parse_yaml_string(payload.globals_yaml)
        g_valid = True
    except Exception as exc:
        g_err = str(exc)

    h_valid, h_dict, h_err = False, {}, None
    if payload.heat_yaml:
        try:
            h_dict = load_template.parse_yaml_string(payload.heat_yaml)
            h_valid = True
        except Exception as exc:
            h_err = str(exc)

    guac_valid, guac_dict, guac_err = False, {}, None
    if payload.guac_yaml:
        try:
            guac_dict = load_template.parse_yaml_string(payload.guac_yaml)
            guac_valid = True
        except Exception as exc:
            guac_err = str(exc)

    globals_data = g_dict.get("globals", {})
    heat_data = g_dict.get("heat", {})
    guac_data = g_dict.get("guacamole", {})

    org = globals_data.get("organization", "cyberrange")
    amount = heat_data.get("amount", globals_data.get("amount", 1))

    heat_resources = []
    if h_dict and isinstance(h_dict, dict):
        for r_name, r_val in h_dict.get("resources", {}).items():
            if isinstance(r_val, dict):
                heat_resources.append({
                    "name": r_name,
                    "type": r_val.get("type", "Unknown"),
                    "is_server": r_val.get("type") in ["OS::Nova::Server", "OS::Heat::ResourceGroup"],
                })

    groups = []
    connections = []
    users = []

    if guac_dict and isinstance(guac_dict, dict):
        for g_name, g_val in guac_dict.get("groups", {}).items():
            groups.append({
                "name": g_name,
                "parent": g_val.get("parent", "ROOT") if isinstance(g_val, dict) else "ROOT",
                "attributes": g_val.get("attributes", {}) if isinstance(g_val, dict) else {},
            })

        for c_name, c_val in guac_dict.get("connectionTemplates", {}).items():
            if isinstance(c_val, dict):
                connections.append({
                    "name": c_name,
                    "parent": c_val.get("parent", "ROOT"),
                    "pattern": c_val.get("pattern", ""),
                    "protocol": c_val.get("protocol", "rdp"),
                    "parameters": c_val.get("parameters", {}),
                })

        for u_name, u_val in guac_dict.get("users", {}).items():
            if isinstance(u_val, dict):
                perms = u_val.get("permissions", {}).get("connectionPermissions", [])
                users.append({
                    "name": u_name,
                    "username": u_val.get("username", u_name),
                    "password": u_val.get("password", "auto-generated"),
                    "connections": perms,
                })

    return {
        "success": g_valid and (not payload.heat_yaml or h_valid) and (not payload.guac_yaml or guac_valid),
        "errors": [e for e in [g_err, h_err, guac_err] if e],
        "summary": {
            "organization": org,
            "stack_count": amount,
            "resource_count": len(heat_resources),
            "group_count": len(groups),
            "connection_count": len(connections),
            "user_count": len(users),
        },
        "heat": {
            "version": h_dict.get("heat_template_version") if h_dict else None,
            "parameters": list(h_dict.get("parameters", {}).keys()) if h_dict else [],
            "resources": heat_resources,
        },
        "guacamole": {
            "groups": groups,
            "connections": connections,
            "users": users,
        },
    }


@router.post("/config/generate")
def generate_range_configuration(payload: GeneratePayload):
    org = payload.organization.strip().replace(" ", "-").lower()

    globals_yaml = f"""# YAML for storing range provisioning parameters
globals:
  debug: false
  artifacts: true
  organization: {org}
  amount: {payload.stack_count}
  provision: true

guacamole:
  provision: true
  update: false
  cloud: guacamole
  guac_file: templates/guac.yaml
  org_name: {org}
  pause: 0.1

heat:
  provision: true
  update: false
  cloud: openstack
  amount: {payload.stack_count}
  heat_file: templates/main.yaml
  stack_name: {org}
  stack_delay: 5
  pause: 0.1
  jinja: true

swift:
  provision: {'true' if payload.enable_swift else 'false'}
  update: false
  cloud: openstack
  assets_dir: assets
  container_name: {org}
  access: private
"""

    guac_yaml = f"""# Guacamole configuration
{{% set systems = {payload.users_per_system} %}}
{{% set organization = "{org}" %}}

stacks:
  - {{{{ organization }}}}

groups:
  {{{{ organization }}}}:
    parent: ROOT
    attributes:
      max-connections: {payload.users_per_system * 2}

connectionTemplates:
  {{{{ organization }}}}.screen.server:
    parent: {{{{ organization }}}}
    pattern: {{{{ organization }}}}.screen.server.(\\d+)
    protocol: {payload.protocol}
    parameters:
      port: {payload.port}
      security: any
      ignore-cert: 'true'
      username: {payload.student_user}
      password: {payload.student_pass}

users:
  {{% for system in range(1, systems + 1) %}}
  {{{{ organization }}}}.user.{{{{ system }}}}:
    username: {{{{ organization }}}}.screen.{{{{ system }}}}
    password: {org.capitalize()}P@ss{{{{ system }}}}!
    permissions:
      connectionPermissions:
        - {{{{ organization }}}}.screen.server.{{{{ system }}}}
  {{% endfor %}}
"""

    heat_yaml = f"""heat_template_version: 2018-03-02
description: Cyber Range Deployment for {org}

parameters:
  username:
    type: string
    default: {payload.student_user}
  password:
    type: string
    default: {payload.student_pass}

resources:
  range_network:
    type: OS::Neutron::Net
    properties:
      name: {org}_network

  range_subnet:
    type: OS::Neutron::Subnet
    properties:
      network_id: {{ get_resource: range_network }}
      cidr: 10.10.10.0/24
      dns_nameservers: [8.8.8.8, 1.1.1.1]

outputs:
  network_id:
    value: {{ get_resource: range_network }}
"""

    return {
        "globals_yaml": globals_yaml,
        "guac_yaml": guac_yaml,
        "heat_yaml": heat_yaml,
    }


@router.post("/config/download-zip")
def download_config_zip(payload: GeneratePayload):
    from fastapi.responses import Response

    data = generate_range_configuration(payload)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("globals.yaml", data["globals_yaml"])
        zf.writestr("templates/guac.yaml", data["guac_yaml"])
        zf.writestr("templates/main.yaml", data["heat_yaml"])
        zf.writestr("assets/config.sh", "#!/bin/bash\necho 'Range initialization script'\n")

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={payload.organization}_range_config.zip"}
    )


@router.post("/provision/run")
async def run_provisioning(payload: ProvisionPayload):
    task_id = str(uuid.uuid4())[:8]

    globals_dict = None
    if payload.globals_yaml:
        try:
            globals_dict = load_template.parse_yaml_string(payload.globals_yaml)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid globals YAML: {e}")
    else:
        # Build globals_dict dynamically from structured parameters or database
        try:
            from src.db.models import SavedRange
            from src.db.database import SessionLocal
            db_session = SessionLocal()
            try:
                if payload.range_id:
                    saved_r = db_session.query(SavedRange).filter(SavedRange.id == payload.range_id).first()
                    if saved_r:
                        globals_dict = saved_r.generate_globals_dict()
                if not globals_dict:
                    temp_range = SavedRange(
                        name="temp",
                        organization=payload.organization or "cyberrange",
                        stack_count=payload.stack_count or 1,
                        users_per_system=payload.users_per_system or 2,
                        protocol=payload.protocol or "rdp",
                        port=payload.port or 3389,
                        student_user=payload.student_user or "student",
                        student_pass=payload.student_pass or "RangeP@ss123!",
                        enable_swift=payload.enable_swift or False,
                        heat_yaml=payload.heat_yaml or "",
                    )
                    globals_dict = temp_range.generate_globals_dict()
            finally:
                db_session.close()
        except Exception as e:
            pass

    clouds_dict = None
    if payload.clouds_yaml:
        try:
            parsed_clouds = load_template.parse_yaml_string(payload.clouds_yaml)
            clouds_dict = parsed_clouds.get("clouds", parsed_clouds)
        except Exception:
            pass
    else:
        # Fallback to SQLite datasources
        try:
            from src.db.database import SessionLocal
            from src.db.models import OpenStackDataSource, GuacamoleDataSource
            db_session = SessionLocal()
            try:
                os_ds = db_session.query(OpenStackDataSource).filter(OpenStackDataSource.is_default == True).first()
                if not os_ds:
                    os_ds = db_session.query(OpenStackDataSource).first()
                guac_ds = db_session.query(GuacamoleDataSource).filter(GuacamoleDataSource.is_default == True).first()
                if not guac_ds:
                    guac_ds = db_session.query(GuacamoleDataSource).first()

                clouds_dict = {}
                if os_ds:
                    c_data = os_ds.to_clouds_dict().get("clouds", {}).get(os_ds.name, {})
                    clouds_dict["openstack"] = c_data
                    clouds_dict["gcr"] = c_data
                if guac_ds:
                    g_data = guac_ds.to_clouds_dict().get("clouds", {}).get(guac_ds.name, {})
                    clouds_dict["guacamole"] = g_data
                    clouds_dict["guac"] = g_data
            finally:
                db_session.close()
        except Exception:
            pass

    TASKS[task_id] = {
        "id": task_id,
        "target": payload.target,
        "action": payload.action,
        "dry_run": payload.dry_run,
        "status": "RUNNING",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "duration": None,
        "logs": [],
        "errors": [],
        "users": [],
    }

    asyncio.create_task(_execute_engine_task(task_id, globals_dict, clouds_dict, payload))

    return {
        "task_id": task_id,
        "status": "RUNNING",
        "dry_run": payload.dry_run,
    }


async def _execute_engine_task(task_id: str, globals_dict: Optional[dict], clouds_dict: Optional[dict], payload: ProvisionPayload):
    task = TASKS[task_id]

    def log_listener(event: ProvisionEvent):
        task["logs"].append(event.to_dict())

    dispatcher.subscribe(log_listener)

    try:
        engine = ProvisionEngine(
            globals_config=globals_dict,
            clouds_config=clouds_dict,
            debug=True,
            dry_run=payload.dry_run,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, engine.run, payload.target, payload.action)

        task["status"] = "SUCCESS" if result.success else "FAILED"
        task["duration"] = result.duration_seconds
        task["errors"] = result.errors

        # Populate provisioned student users
        if payload.guac_yaml:
            try:
                guac_data = load_template.parse_yaml_string(payload.guac_yaml)
                for u_key, u_val in guac_data.get("users", {}).items():
                    if isinstance(u_val, dict):
                        task["users"].append({
                            "key": u_key,
                            "username": u_val.get("username", u_key),
                            "password": u_val.get("password", "generated"),
                            "connections": ", ".join(u_val.get("permissions", {}).get("connectionPermissions", [])),
                        })
            except Exception:
                pass
        elif payload.organization and payload.users_per_system:
            org = payload.organization.strip().replace(" ", "-").lower()
            total_students = (payload.stack_count or 1) * payload.users_per_system
            for s in range(1, total_students + 1):
                task["users"].append({
                    "key": f"{org}.user.{s}",
                    "username": f"{org}.screen.{s}",
                    "password": payload.student_pass or "auto-generated",
                    "connections": f"{org}.screen.server.{s}",
                })


    except Exception as exc:
        task["status"] = "FAILED"
        task["errors"].append(str(exc))
    finally:
        dispatcher.unsubscribe(log_listener)
        task["end_time"] = datetime.now().isoformat()


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/users")
def get_task_users(task_id: str, format: str = "json"):
    import csv
    from fastapi.responses import Response

    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    users = task.get("users", [])
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["key", "username", "password", "connections"])
        writer.writeheader()
        writer.writerows(users)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=users_{task_id}.csv"}
        )

    return {"users": users}


@router.websocket("/ws/tasks/{task_id}")
async def websocket_logs(websocket: WebSocket, task_id: str):
    await websocket.accept()
    log_queue = asyncio.Queue()
    dispatcher.register_async_queue(log_queue)

    task = TASKS.get(task_id)
    if task:
        for log in task.get("logs", []):
            await websocket.send_json(log)

    try:
        while True:
            if task and task["status"] in ["SUCCESS", "FAILED"] and log_queue.empty():
                await websocket.send_json({"level": "COMPLETE", "message": f"Task completed: {task['status']}"})
                break

            try:
                event = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                await websocket.send_json(event.to_dict())
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        dispatcher.unregister_async_queue(log_queue)


@router.get("/presets")
def get_template_presets():
    presets = [
        {
            "id": "kali-pentest",
            "name": "Kali Linux Penetration Testing Range",
            "description": "2 Kali attacking systems with dedicated RDP GUI connections and a vulnerable target stack.",
            "protocol": "rdp",
            "port": 3389,
            "stack_count": 2,
            "users_per_system": 2,
            "student_user": "kali",
            "student_pass": "kali",
        },
        {
            "id": "ctf-challenge",
            "name": "CTF Competition Blue/Red Team",
            "description": "Multi-team competitive cyber range with 4 isolated student stacks and centralized scoring.",
            "protocol": "ssh",
            "port": 22,
            "stack_count": 4,
            "users_per_system": 4,
            "student_user": "competitor",
            "student_pass": "CTF@2026Challenge!",
        },
        {
            "id": "soc-training",
            "name": "SOC Analyst Defensive Range",
            "description": "Defensive monitoring environment with analyst workstations, SIEM dashboards, and RDP access.",
            "protocol": "rdp",
            "port": 3389,
            "stack_count": 1,
            "users_per_system": 5,
            "student_user": "analyst",
            "student_pass": "DefendTheRange2026!",
        }
    ]
    return {"presets": presets}

