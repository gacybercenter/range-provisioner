"""
Unified Provisioning Engine and Orchestrator for Range Provisioner.
Coordinates validation, OpenStack, Swift, Heat, and Guacamole actions.
Supports both live execution and dry-run simulation with real-time event streaming.
"""
import os
import time
import traceback
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    from src.config.models import RangeConfig
    from src.config.validator import validate_range_package, ValidationResult
    from src.utils import msg_format, load_template, connections
    from src.utils.events import dispatcher, ProvisionEvent
    from src.provision import heat, swift, guac
except ImportError:
    from config.models import RangeConfig
    from config.validator import validate_range_package, ValidationResult
    from utils import msg_format, load_template, connections
    from utils.events import dispatcher, ProvisionEvent
    from provision import heat, swift, guac


@dataclass
class ProvisioningPlan:
    target: str
    action: str
    dry_run: bool
    stacks_to_create: List[str] = field(default_factory=list)
    stacks_to_delete: List[str] = field(default_factory=list)
    containers_to_create: List[str] = field(default_factory=list)
    guac_groups: List[str] = field(default_factory=list)
    guac_connections: List[str] = field(default_factory=list)
    guac_users: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ProvisioningResult:
    success: bool
    duration_seconds: float
    target: str
    action: str
    dry_run: bool
    stacks: Dict[str, Any] = field(default_factory=dict)
    instances: Dict[str, str] = field(default_factory=dict)
    guac_connections: List[Dict[str, Any]] = field(default_factory=list)
    users: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)


class MockOpenStackConnection:
    def __init__(self):
        self.orchestration = self
        self.object_store = self

    def list_servers(self, filters=None):
        return [
            {"id": "mock-srv-1", "name": "automation.server.1", "public_v4": "192.168.1.101", "private_v4": "10.0.0.101"},
            {"id": "mock-srv-2", "name": "automation.server.2", "public_v4": "192.168.1.102", "private_v4": "10.0.0.102"},
        ]

    def get_server(self, name_or_id):
        return {
            "id": name_or_id,
            "name": f"server-{name_or_id}",
            "public_v4": "192.168.1.50",
            "private_v4": "10.0.0.50",
        }

    def create_stack(self, **kwargs):
        return {"id": "mock-stack-id", "name": kwargs.get("name"), "status": "CREATE_COMPLETE"}

    def update_stack(self, **kwargs):
        return {"id": "mock-stack-id", "name": kwargs.get("name_or_id"), "status": "UPDATE_COMPLETE"}

    def delete_stack(self, **kwargs):
        return None

    def get_stack(self, name_or_id):
        return None

    def resources(self, name):
        return []

    def create_container(self, **kwargs):
        return {"name": kwargs.get("name")}

    def delete_container(self, **kwargs):
        return None

    def search_containers(self, **kwargs):
        return []

    def set_container_access(self, **kwargs):
        return {"name": kwargs.get("name"), "access": kwargs.get("access")}

    def create_directory_marker_object(self, **kwargs):
        return None

    def create_object(self, **kwargs):
        return None

    def delete_object(self, **kwargs):
        return True

    def list_objects(self, name):
        return []


class MockGuacamoleSession:
    def __init__(self):
        self.created_groups = []
        self.created_conns = []
        self.created_users = []

    def detail_connection_group_connections(self, identifier):
        return {"name": "ROOT", "identifier": "ROOT", "childConnectionGroups": [], "childConnections": []}

    def create_connection_group(self, name, group_type, parent, attributes):
        self.created_groups.append(name)
        return {"identifier": f"mock-grp-{name}", "name": name, "parentIdentifier": parent}

    def update_connection_group(self, identifier, name, group_type, parent, attributes):
        return {"identifier": identifier, "name": name}

    def delete_connection_group(self, identifier):
        return None

    def create_connection(self, name, protocol, parent, parameters, attributes):
        self.created_conns.append(name)
        return {"identifier": f"mock-conn-{name}", "name": name, "parentIdentifier": parent}

    def update_connection(self, identifier, name, protocol, parent, parameters, attributes):
        return {"identifier": identifier, "name": name}

    def delete_connection(self, identifier):
        return None

    def list_connection_groups(self):
        return {}

    def list_connections(self):
        return {}

    def list_sharing_profiles(self):
        return {}

    def list_users(self):
        return {}

    def create_user(self, username, password, attributes):
        self.created_users.append(username)
        return {"username": username}

    def update_user(self, username, password, attributes):
        return {"username": username}

    def delete_user(self, username):
        return None

    def detail_user_permissions(self, username):
        return {}

    def assign_user_permissions(self, username, permissions):
        return None


class ProvisionEngine:
    def __init__(self,
                 globals_config: Optional[Dict[str, Any]] = None,
                 clouds_config: Optional[Dict[str, Any]] = None,
                 globals_path: str = "globals.yaml",
                 clouds_path: str = "clouds.yaml",
                 debug: bool = False,
                 dry_run: bool = False):
        self.globals_path = globals_path
        self.clouds_path = clouds_path
        self.debug = debug
        self.dry_run = dry_run

        self.globals_dict: Dict[str, Any] = globals_config or {}
        self.clouds_dict: Dict[str, Any] = clouds_config or {}

    def load_configurations(self) -> None:
        if not self.globals_dict and os.path.exists(self.globals_path):
            self.globals_dict = load_template.load_template(self.globals_path) or {}

        if not self.clouds_dict and os.path.exists(self.clouds_path):
            try:
                loaded = load_template.load_template(self.clouds_path)
                if loaded and "clouds" in loaded:
                    self.clouds_dict = loaded["clouds"]
                elif loaded:
                    self.clouds_dict = loaded
            except Exception as e:
                msg_format.info_msg(f"Could not load clouds.yaml: {e}", "Engine", self.debug)

        # Fall back or augment with datasources stored in SQLite database
        try:
            try:
                from src.db.database import SessionLocal
                from src.db.models import OpenStackDataSource, GuacamoleDataSource
            except ImportError:
                from db.database import SessionLocal
                from db.models import OpenStackDataSource, GuacamoleDataSource

            with SessionLocal() as db:
                ostack_sources = db.query(OpenStackDataSource).all()
                for os_ds in ostack_sources:
                    if os_ds.name not in self.clouds_dict:
                        self.clouds_dict[os_ds.name] = os_ds.to_clouds_dict()
                    if os_ds.is_default and "openstack" not in self.clouds_dict:
                        self.clouds_dict["openstack"] = os_ds.to_clouds_dict()

                guac_sources = db.query(GuacamoleDataSource).all()
                for g_ds in guac_sources:
                    if g_ds.name not in self.clouds_dict:
                        self.clouds_dict[g_ds.name] = g_ds.to_clouds_dict()
                    if g_ds.is_default and "guacamole" not in self.clouds_dict:
                        self.clouds_dict["guacamole"] = g_ds.to_clouds_dict()
        except Exception as e:
            if self.debug:
                msg_format.info_msg(f"SQLite datasource lookup skipped: {e}", "Engine", self.debug)


    def plan(self,
             target: str = "full",
             action: str = "create") -> ProvisioningPlan:
        self.load_configurations()
        plan = ProvisioningPlan(target=target, action=action, dry_run=self.dry_run)

        globals_data = self.globals_dict.get("globals", {})
        org = globals_data.get("organization", "range")
        heat_data = self.globals_dict.get("heat", {})
        guac_data = self.globals_dict.get("guacamole", {})
        swift_data = self.globals_dict.get("swift", {})

        if target in ["full", "heat"]:
            stack_name = heat_data.get("stack_name", org)
            amount = heat_data.get("amount", globals_data.get("amount", 1))
            from src.utils.generate import generate_names
            stacks = generate_names(amount, stack_name)
            if action in ["create", "update"]:
                plan.stacks_to_create.extend(stacks)
            else:
                plan.stacks_to_delete.extend(stacks)

        if target in ["full", "guacamole"]:
            conn_params = guac_data.get("conn_params")
            if not conn_params:
                guac_file = guac_data.get("guac_file", "templates/guac.yaml")
                template_dir = globals_data.get("template_dir", "templates")
                try:
                    conn_params = load_template.load_yaml_file(guac_file, template_dir, self.debug)
                except Exception as exc:
                    plan.warnings.append(f"Could not parse Guacamole template for planning: {exc}")

            if conn_params:
                plan.guac_groups = list(conn_params.get("groups", {}).keys())
                plan.guac_connections = list(conn_params.get("connectionTemplates", {}).keys())
                plan.guac_users = list(conn_params.get("users", {}).keys())


        if target in ["full", "swift"] and swift_data.get("provision", False):
            c_name = swift_data.get("container_name", org)
            plan.containers_to_create.append(c_name)

        return plan

    def run(self,
            target: str = "full",
            action: Optional[str] = None,
            delay_override: Optional[float] = None) -> ProvisioningResult:
        start_time = time.time()
        endpoint = "Provisioner"
        result = ProvisioningResult(
            success=False,
            duration_seconds=0.0,
            target=target,
            action=action or "create",
            dry_run=self.dry_run,
        )

        msg_format.general_msg(f"Initiating Range Provisioner [Target: {target}, DryRun: {self.dry_run}]...", endpoint)

        try:
            self.load_configurations()

            if not self.globals_dict:
                raise ValueError("Globals configuration is empty or could not be loaded")

            globals_settings = self.globals_dict.get("globals", {})
            heat_settings = self.globals_dict.get("heat", {})
            guac_settings = self.globals_dict.get("guacamole", {})
            swift_settings = self.globals_dict.get("swift", {})

            if delay_override is not None:
                heat_settings["pause"] = delay_override
                heat_settings["stack_delay"] = delay_override
                guac_settings["pause"] = delay_override
                if swift_settings:
                    swift_settings["pause"] = delay_override
            elif self.dry_run:
                heat_settings["stack_delay"] = 0
                heat_settings["pause"] = 0
                guac_settings["pause"] = 0
                if swift_settings:
                    swift_settings["pause"] = 0

            if action:
                if action == "create":
                    globals_settings["provision"] = True
                    heat_settings["update"] = False
                    guac_settings["update"] = False
                elif action == "update":
                    globals_settings["provision"] = True
                    heat_settings["update"] = True
                    guac_settings["update"] = True
                elif action == "delete":
                    globals_settings["provision"] = False

            oconn = None
            gconn = None

            if self.dry_run:
                msg_format.general_msg("[DRY-RUN] Simulating API connections...", endpoint)
                oconn = MockOpenStackConnection()
                gconn = MockGuacamoleSession()
            else:
                if target in ["full", "heat", "swift"]:
                    cloud_name = heat_settings.get("cloud", "openstack")
                    if cloud_name in self.clouds_dict:
                        oconn = connections.openstack_connection(cloud_name, self.clouds_dict[cloud_name], self.debug)
                    else:
                        raise KeyError(f"OpenStack cloud '{cloud_name}' not found in clouds configuration")

                if target in ["full", "guacamole"]:
                    g_cloud_name = guac_settings.get("cloud", "guacamole")
                    if g_cloud_name in self.clouds_dict:
                        gconn = connections.guacamole_connection(g_cloud_name, self.clouds_dict[g_cloud_name], self.debug)
                    else:
                        raise KeyError(f"Guacamole cloud '{g_cloud_name}' not found in clouds configuration")

            if target in ["full", "swift"] and swift_settings:
                msg_format.general_msg("Provisioning Swift Object Storage...", "Swift")
                swift.provision(oconn, globals_settings, swift_settings, self.debug)

            if target in ["full", "heat"]:
                msg_format.general_msg("Provisioning Heat Orchestration Stacks...", "Heat")
                heat.provision(oconn, globals_settings, heat_settings, self.debug)

            if target in ["full", "guacamole"]:
                msg_format.general_msg("Provisioning Guacamole...", "Guacamole")
                guac.provision(oconn, gconn, globals_settings, guac_settings, self.debug)

            result.success = True
            msg_format.success_msg("Range provisioning completed successfully.", endpoint)

        except Exception as exc:
            err_msg = f"{exc}\n{traceback.format_exc()}"
            msg_format.error_msg(err_msg, endpoint)
            result.errors.append(str(exc))
            result.success = False

        result.duration_seconds = round(time.time() - start_time, 2)
        result.logs = [ev.to_dict() for ev in dispatcher.event_history[-100:]]
        return result
