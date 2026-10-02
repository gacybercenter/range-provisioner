"""
Configuration data models and schemas for Range Provisioner
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class GlobalsSettings(BaseModel):
    debug: bool = Field(default=False, description="Enable debug logging")
    artifacts: bool = Field(default=True, description="Save/display artifacts")
    organization: str = Field(default="range", description="Top-level organization identifier")
    template_dir: Optional[str] = Field(default="templates", description="Directory containing templates")
    provision: Optional[bool] = Field(default=None, description="Master provision flag")
    amount: Optional[int] = Field(default=1, description="Default number of ranges/stacks to provision")


class GuacamoleSettings(BaseModel):
    provision: bool = Field(default=True, description="Provision Guacamole resources")
    update: bool = Field(default=False, description="Update existing Guacamole resources")
    cloud: str = Field(default="guacamole", description="Cloud/credentials key in clouds.yaml")
    guac_file: str = Field(default="templates/guac.yaml", description="Path to Guacamole YAML template")
    org_name: Optional[str] = Field(default=None, description="Guacamole organization name")
    pause: float = Field(default=0.0, description="Pause between Guacamole actions in seconds")


class HeatSettings(BaseModel):
    provision: bool = Field(default=True, description="Provision Heat orchestration stacks")
    update: bool = Field(default=False, description="Update existing Heat stacks")
    cloud: str = Field(default="openstack", description="OpenStack cloud identifier in clouds.yaml")
    amount: int = Field(default=1, description="Number of Heat stacks to provision")
    heat_file: str = Field(default="templates/main.yaml", description="Path to Heat template YAML")
    stack_name: Optional[str] = Field(default=None, description="Base stack name")
    stack_delay: float = Field(default=5.0, description="Delay between each stack creation in seconds")
    pause: float = Field(default=0.0, description="Pause between Heat API actions in seconds")
    jinja: bool = Field(default=False, description="Render Heat template using Jinja2")
    parameters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Overrides for Heat stack parameters")


class SwiftSettings(BaseModel):
    provision: bool = Field(default=False, description="Provision Swift object store")
    update: bool = Field(default=False, description="Update Swift object store")
    cloud: str = Field(default="openstack", description="OpenStack cloud identifier in clouds.yaml")
    assets_dir: str = Field(default="assets", description="Directory containing assets to upload")
    container_name: Optional[str] = Field(default=None, description="Swift container name")
    pause: float = Field(default=0.0, description="Pause between Swift API actions in seconds")


class RangeConfig(BaseModel):
    globals: GlobalsSettings = Field(default_factory=GlobalsSettings)
    guacamole: GuacamoleSettings = Field(default_factory=GuacamoleSettings)
    heat: HeatSettings = Field(default_factory=HeatSettings)
    swift: Optional[SwiftSettings] = Field(default_factory=SwiftSettings)


class GuacConnectionTemplate(BaseModel):
    parent: Optional[str] = Field(default=None, description="Parent connection group name")
    pattern: Optional[str] = Field(default=None, description="Regex pattern to match server hostname/IP")
    protocol: str = Field(default="rdp", description="Protocol: rdp, ssh, vnc")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Connection parameters")


class GuacGroupDefinition(BaseModel):
    parent: str = Field(default="ROOT", description="Parent connection group (e.g. ROOT)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Group attributes")


class GuacUserDefinition(BaseModel):
    username: str = Field(..., description="Username")
    password: Optional[str] = Field(default=None, description="Password")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="User attributes")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="User permissions dictionary")


class GuacConfig(BaseModel):
    stacks: Optional[List[str]] = Field(default_factory=list, description="Associated Heat stack names")
    groups: Dict[str, GuacGroupDefinition] = Field(default_factory=dict, description="Connection group definitions")
    connectionTemplates: Dict[str, GuacConnectionTemplate] = Field(default_factory=dict, description="Connection templates")
    users: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User definitions")
    defaults: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Default parameter overrides")
