"""Load optional Heat parameter values and resolve existing network IDs."""

from typing import Any
from openstack.connection import Connection
from utils import load_template


def load_parameters(conn: Connection, filename: str, template_dir: str | None,
                    stacks: list[str]) -> dict[str, Any]:
    data = load_template.load_yaml_file(filename, template_dir)
    if set(data) != {'parameters'} or not isinstance(data['parameters'], dict):
        raise ValueError(
            "Heat env file must contain only a 'parameters' mapping."
        )
    parameters = data['parameters'].copy()
    if not all(isinstance(key, str) and key for key in parameters):
        raise ValueError("Heat env parameter names must be nonempty strings.")

    found = {}
    for stack in stacks:
        for resource in conn.orchestration.resources(stack):
            resource_type = resource.resource_type
            if resource_type not in {'OS::Neutron::Net', 'OS::Neutron::Subnet'}:
                continue
            if not resource.physical_resource_id:
                raise ValueError(
                    f"Missing physical ID for resource '{resource.logical_resource_id}' "
                    f"in stack '{stack}'."
                )
            if resource_type == 'OS::Neutron::Net':
                network = conn.network.find_network(resource.physical_resource_id)
            else:
                network = conn.network.find_subnet(resource.physical_resource_id)
            if network is None or not network.name:
                raise ValueError(
                    f"Cannot resolve {resource_type} resource "
                    f"'{resource.logical_resource_id}' in stack '{stack}'."
                )
            name = network.name
            for prefix in (f'{stack}-', f'{stack}.'):
                if name.startswith(prefix):
                    name = name[len(prefix):]
                    break
            key = f'{name}_id'
            if key not in parameters:
                continue
            if key in found and found[key] != resource.physical_resource_id:
                raise ValueError(f"Multiple resources match Heat env parameter '{key}'.")
            found[key] = resource.physical_resource_id

    unresolved = [
        key for key, value in parameters.items()
        if stacks and key.endswith('_id') and value is None and key not in found
    ]
    if unresolved:
        raise ValueError(f"Could not resolve Heat env parameters: {', '.join(unresolved)}.")

    parameters.update(found)
    return parameters
