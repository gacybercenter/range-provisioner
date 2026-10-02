"""
Configuration validators and analyzers for Range Provisioner
"""
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Union
import yaml
from jinja2 import Environment, TemplateSyntaxError

from .models import RangeConfig, GuacConfig


class ValidationResult:
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: Dict[str, Any] = {}

    def add_error(self, message: str) -> None:
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


def validate_yaml_syntax(content: str, name: str = "YAML") -> Tuple[bool, Optional[Any], Optional[str]]:
    try:
        data = yaml.safe_load(content)
        return True, data, None
    except yaml.YAMLError as exc:
        mark = getattr(exc, 'problem_mark', None)
        line_info = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
        return False, None, f"YAML syntax error in {name}{line_info}: {exc}"


def render_jinja_string(content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    try:
        env = Environment()
        template = env.from_string(content)
        rendered = template.render(context or {})
        return True, rendered, None
    except TemplateSyntaxError as exc:
        return False, None, f"Jinja syntax error on line {exc.lineno}: {exc.message}"
    except Exception as exc:
        return False, None, f"Template rendering error: {str(exc)}"


def validate_globals(content_or_dict: Union[str, Dict[str, Any]]) -> ValidationResult:
    result = ValidationResult()

    if isinstance(content_or_dict, str):
        valid, data, err = validate_yaml_syntax(content_or_dict, "globals.yaml")
        if not valid:
            result.add_error(err)
            return result
    else:
        data = content_or_dict

    if not isinstance(data, dict):
        result.add_error("globals.yaml must be a dictionary/mapping")
        return result

    if "globals" not in data:
        result.add_warning("Missing top-level 'globals' key; defaults will be applied")

    try:
        cfg = RangeConfig.model_validate(data)
        result.info["organization"] = cfg.globals.organization
        result.info["heat_cloud"] = cfg.heat.cloud if cfg.heat else None
        result.info["guac_cloud"] = cfg.guacamole.cloud if cfg.guacamole else None
        result.info["heat_stacks_amount"] = cfg.heat.amount if cfg.heat else 1
    except Exception as exc:
        result.add_error(f"Globals schema validation failed: {str(exc)}")

    return result


def validate_heat_template(content_or_dict: Any) -> ValidationResult:
    result = ValidationResult()

    if isinstance(content_or_dict, str):
        is_jinja, rendered, j_err = render_jinja_string(content_or_dict)
        yaml_content = rendered if is_jinja and rendered else content_or_dict
        valid, data, err = validate_yaml_syntax(yaml_content, "Heat template")
        if not valid:
            result.add_error(err)
            return result
    else:
        data = content_or_dict

    if not isinstance(data, dict):
        result.add_error("Heat template must be a YAML dictionary")
        return result

    hot_version = data.get("heat_template_version")
    if not hot_version:
        result.add_warning("Missing 'heat_template_version' declaration in Heat template")
    else:
        result.info["heat_template_version"] = str(hot_version)

    resources = data.get("resources", {})
    if not resources or not isinstance(resources, dict):
        result.add_error("Heat template has no 'resources' section or it is not a dictionary")
    else:
        server_resources = [
            k for k, v in resources.items()
            if isinstance(v, dict) and v.get("type") in ["OS::Nova::Server", "OS::Heat::ResourceGroup"]
        ]
        result.info["total_resources"] = len(resources)
        result.info["server_resources"] = server_resources
        result.info["server_count"] = len(server_resources)

    params = data.get("parameters", {})
    if isinstance(params, dict):
        result.info["parameters"] = list(params.keys())

    return result


def validate_guacamole_template(content_or_dict: Any) -> ValidationResult:
    result = ValidationResult()

    if isinstance(content_or_dict, str):
        is_jinja, rendered, j_err = render_jinja_string(content_or_dict)
        yaml_content = rendered if is_jinja and rendered else content_or_dict
        valid, data, err = validate_yaml_syntax(yaml_content, "Guacamole template")
        if not valid:
            result.add_error(err)
            return result
    else:
        data = content_or_dict

    if not isinstance(data, dict):
        result.add_error("Guacamole template must be a YAML dictionary")
        return result

    groups = data.get("groups", {})
    conn_templates = data.get("connectionTemplates", {})
    users = data.get("users", {})

    if not groups:
        result.add_error("No 'groups' section found in Guacamole template")
    elif not isinstance(groups, dict):
        result.add_error("'groups' must be a dictionary of connection groups")
    else:
        result.info["group_count"] = len(groups)
        result.info["groups"] = list(groups.keys())

    if not conn_templates:
        result.add_warning("No 'connectionTemplates' defined in Guacamole template")
    elif isinstance(conn_templates, dict):
        result.info["connection_count"] = len(conn_templates)
        result.info["connection_templates"] = list(conn_templates.keys())

    if users and isinstance(users, dict):
        result.info["user_count"] = len(users)
        result.info["users"] = list(users.keys())

    if isinstance(groups, dict):
        group_names = set(groups.keys())
        for name, gdata in groups.items():
            if isinstance(gdata, dict):
                parent = gdata.get("parent")
                if parent and parent != "ROOT" and parent not in group_names:
                    result.add_warning(f"Connection group '{name}' references non-existent parent '{parent}'")

    return result


def validate_range_package(globals_data: Any, heat_data: Optional[Any] = None, guac_data: Optional[Any] = None) -> ValidationResult:
    result = ValidationResult()

    g_res = validate_globals(globals_data)
    result.errors.extend(g_res.errors)
    result.warnings.extend(g_res.warnings)
    result.info["globals"] = g_res.info

    if heat_data is not None:
        h_res = validate_heat_template(heat_data)
        result.errors.extend(h_res.errors)
        result.warnings.extend(h_res.warnings)
        result.info["heat"] = h_res.info

    if guac_data is not None:
        gu_res = validate_guacamole_template(guac_data)
        result.errors.extend(gu_res.errors)
        result.warnings.extend(gu_res.warnings)
        result.info["guacamole"] = gu_res.info

    result.is_valid = len(result.errors) == 0
    return result

