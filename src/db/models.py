"""
SQLAlchemy database models for Users, Datasources, Range Projects, and Task Logs.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="operator", nullable=False)  # 'admin', 'operator', 'viewer'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class OpenStackDataSource(Base):
    __tablename__ = "openstack_datasources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    auth_url = Column(String(256), nullable=False)
    username = Column(String(128), nullable=False)
    password = Column(String(256), nullable=False)
    project_name = Column(String(128), nullable=False)
    user_domain_name = Column(String(64), default="Default", nullable=False)
    project_domain_name = Column(String(64), default="Default", nullable=False)
    region_name = Column(String(64), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_clouds_dict(self) -> dict:
        """Convert database record to OpenStackSDK clouds.yaml dictionary format."""
        auth_dict = {
            "auth_url": self.auth_url,
            "username": self.username,
            "password": self.password,
            "project_name": self.project_name,
            "user_domain_name": self.user_domain_name,
            "project_domain_name": self.project_domain_name,
        }
        cloud_dict = {
            "auth": auth_dict,
            "identity_api_version": 3,
        }
        if self.region_name:
            cloud_dict["region_name"] = self.region_name
        return cloud_dict


class GuacamoleDataSource(Base):
    __tablename__ = "guacamole_datasources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    host = Column(String(256), nullable=False)
    data_source = Column(String(64), default="mysql", nullable=False)
    username = Column(String(128), nullable=False)
    password = Column(String(256), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_clouds_dict(self) -> dict:
        """Convert database record to guacamole session config format."""
        return {
            "host": self.host,
            "data_source": self.data_source,
            "username": self.username,
            "password": self.password,
        }


class SavedRange(Base):
    __tablename__ = "saved_ranges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    organization = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    stack_count = Column(Integer, default=1, nullable=False)
    users_per_system = Column(Integer, default=2, nullable=False)
    protocol = Column(String(32), default="rdp", nullable=False)
    port = Column(Integer, default=3389, nullable=False)
    student_user = Column(String(64), default="student", nullable=False)
    student_pass = Column(String(64), default="RangeP@ss123!", nullable=False)
    enable_swift = Column(Boolean, default=False, nullable=False)
    heat_yaml = Column(Text, nullable=False, default="")
    globals_yaml = Column(Text, nullable=True, default="")
    guac_yaml = Column(Text, nullable=True, default="")
    config_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __init__(self, **kwargs):
        if kwargs.get("globals_yaml") is None:
            kwargs["globals_yaml"] = ""
        if kwargs.get("guac_yaml") is None:
            kwargs["guac_yaml"] = ""
        if kwargs.get("config_json") is None:
            kwargs["config_json"] = "{}"
        super().__init__(**kwargs)


    def generate_guac_params(self) -> dict:
        """Dynamically generate Guacamole connection and users structure in memory without guac.yaml."""
        org = self.organization.strip().replace(" ", "-").lower()
        total_systems = self.users_per_system * self.stack_count
        return {
            "stacks": [org],
            "groups": {
                org: {
                    "parent": "ROOT",
                    "attributes": {
                        "max-connections": total_systems * 2,
                    }
                }
            },
            "connectionTemplates": {
                f"{org}.screen.server": {
                    "parent": org,
                    "pattern": rf"{org}\.screen\.server\.(\d+)",
                    "protocol": self.protocol,
                    "parameters": {
                        "port": self.port,
                        "security": "any",
                        "ignore-cert": "true",
                        "username": self.student_user,
                        "password": self.student_pass,
                    }
                }
            },
            "users": {
                f"{org}.user.{sys_id}": {
                    "username": f"{org}.screen.{sys_id}",
                    "password": f"{org.capitalize()}P@ss{sys_id}!",
                    "permissions": {
                        "connectionPermissions": [f"{org}.screen.server.{sys_id}"]
                    }
                }
                for sys_id in range(1, total_systems + 1)
            }
        }

    def generate_globals_dict(self) -> dict:
        """Dynamically produce engine runtime configuration dictionary without globals.yaml."""
        org = self.organization.strip().replace(" ", "-").lower()
        return {
            "globals": {
                "debug": True,
                "artifacts": True,
                "organization": org,
                "amount": self.stack_count,
                "provision": True,
            },
            "guacamole": {
                "provision": True,
                "update": False,
                "cloud": "guacamole",
                "org_name": org,
                "pause": 0.1,
                "conn_params": self.generate_guac_params(),
            },
            "heat": {
                "provision": True,
                "update": False,
                "cloud": "openstack",
                "amount": self.stack_count,
                "stack_name": org,
                "stack_delay": 0.1,
                "pause": 0.1,
                "jinja": False,
                "heat_template_yaml": self.heat_yaml,
            },
            "swift": {
                "provision": self.enable_swift,
                "update": False,
                "cloud": "openstack",
                "container_name": org,
                "access": "private",
            }
        }


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    prefix = Column(String(16), nullable=False)
    key_hash = Column(String(64), index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="api_keys")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True, index=True)
    value = Column(Text, nullable=False, default="")
    category = Column(String(64), default="general", nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    range_id = Column(Integer, ForeignKey("saved_ranges.id", ondelete="SET NULL"), nullable=True)
    target = Column(String(32), default="full", nullable=False)  # 'full', 'openstack', 'guacamole', 'swift'
    dry_run = Column(Boolean, default=False, nullable=False)
    build_at = Column(DateTime, nullable=True)  # Scheduled provisioning datetime (UTC)
    delete_at = Column(DateTime, nullable=True)  # Scheduled deprovisioning datetime (UTC)
    build_status = Column(String(32), default="pending", nullable=False)  # 'scheduled', 'in_progress', 'completed', 'failed', 'cancelled', 'skipped'
    delete_status = Column(String(32), default="pending", nullable=False)  # 'scheduled', 'in_progress', 'completed', 'failed', 'cancelled', 'skipped'
    build_log = Column(Text, nullable=True, default="")
    delete_log = Column(Text, nullable=True, default="")
    config_json = Column(Text, nullable=True, default="{}")
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    range = relationship("SavedRange", backref="schedules")
    created_by = relationship("User", backref="created_schedules")



