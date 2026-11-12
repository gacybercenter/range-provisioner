"""Load and apply named range configuration overrides."""

from copy import deepcopy
from pathlib import Path
from typing import Any

from utils import load_template


_SECTIONS = frozenset({'globals', 'heat', 'guacamole', 'swift'})


def _merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def apply_range(config: dict[str, Any], name: str, filename: str) -> dict[str, Any]:
    """Overlay one named range onto the base configuration without mutating it."""
    path = Path(filename)
    data = load_template.load_yaml_file(path.name, str(path.parent))
    ranges = data.get('ranges')
    if not isinstance(ranges, dict):
        raise ValueError(f"'{filename}' must contain a 'ranges' mapping.")
    if name not in ranges:
        raise ValueError(f"Range '{name}' was not found in '{filename}'.")
    overrides = ranges[name]
    if not isinstance(overrides, dict):
        raise ValueError(f"Range '{name}' must be a mapping of configuration sections.")

    for section, value in overrides.items():
        if section not in _SECTIONS:
            raise ValueError(f"Unknown section '{section}' in range '{name}'.")
        if not isinstance(value, dict):
            raise ValueError(f"Section '{section}' in range '{name}' must be a mapping.")
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Base configuration section '{section}' must be a mapping.")

    return _merge(config, overrides)
