"""
Handles the logic for generating Heat and Guacamole data
"""
import os
from typing import TypedDict
from utils import msg_format


class MultiStackEnvironment(TypedDict):
    num_ranges: int
    org_name: str | None
    range_number: str | None
    domain_name: str | None
    domain_netbios_name: str | None
    cs_number: str | None
    csToken: str | None


def read_multi_stack_environment() -> MultiStackEnvironment:
    """Read and validate multi-stack values when provisioning starts."""
    try:
        num_ranges = int(os.getenv("num_ranges", "1"))
    except ValueError as error:
        raise ValueError(
            "Environment variable 'num_ranges' must be a positive integer."
        ) from error

    if num_ranges < 1:
        raise ValueError(
            "Environment variable 'num_ranges' must be a positive integer."
        )

    return {
        'num_ranges': num_ranges,
        'org_name': os.getenv('org_name'),
        'range_number': os.getenv('range_number'),
        'domain_name': os.getenv('domain_name'),
        'domain_netbios_name': os.getenv('domain_netbios_name'),
        'cs_number': os.getenv('cs_number'),
        'csToken': os.getenv('csToken'),
    }


def generate_names(ranges: int,
                   prefix: str) -> list:
    """
    Generate a list of names with a prefix and a range of numbers

    Args:
        ranges (int): The number of names to generate.
        prefix (str): The prefix for the names.

    Returns:
        list: The generated names
    """

    if not isinstance(ranges, int) or isinstance(ranges, bool) or ranges < 1:
        raise ValueError("'ranges' must be a positive integer.")
    if not prefix:
        raise ValueError("'prefix' must not be empty.")

    if ranges == 1:
        return [prefix]

    return [f"{prefix}.{i+1}" for i in range(ranges)]


def set_provisioning_flags(global_create: bool | None,
                           local_create: bool,
                           local_update: bool = False,
                           endpoint: str = '',
                           debug: bool = False) -> bool:
    """
    Sets provisioning and update flags based on global and local settings.

    If global_create is True, it sets the provision to global_create and update to local_update.
    If global_create is False, it checks the local_create and local_update, and raises an error
    if local_create is False and local_update is True.
    Logs the provisioning and update status if debug is True.

    Args:
        global_create (bool): The global flag indicating if provisioning should occur.
        local_create (bool): The local flag indicating if provisioning should occur.
        local_update (bool, optional): The local flag indicating if an update should occur. Defaults to False.
        endpoint (str, optional): The endpoint name for logging purposes. Defaults to ''.
        debug (bool, optional): A flag determining whether debug information should be printed. Defaults to False.

    Returns:
        bool: True if the settings are valid, False otherwise with an error message logged.
    """

    # Set the create and update flags based on the provided arguments
    create = local_create if global_create is None else global_create
    update = local_update

    if create is None and update:
        raise Exception(
            f"Invalid provisioning and update flags: create={create}, update={update}"
        )

    # Log the provisioning and update status if debug is enabled
    msg_format.info_msg(f"The {endpoint} provision flag is set to '{create}'",
                        endpoint,
                        debug)
    msg_format.info_msg(f"The {endpoint} update flag is set to '{update}'",
                        endpoint,
                        debug)

    return create, update


def update_heat_params(heat_globals: dict,
                       heat_params: dict,
                       endpoint: str = '',
                       debug: bool = False,
                       multi_stack_environment: MultiStackEnvironment | None = None,
                       env_parameters: dict | None = None) -> dict:
    """
    Updates the heat parameters based on the heat globals.
    """
    if multi_stack_environment is None:
        multi_stack_environment = read_multi_stack_environment()

    msg_format.general_msg(f"Updating heat parameters with global values.",
                           endpoint)
    
    if not isinstance(heat_params, dict):
        raise ValueError("Heat template 'parameters' must be a mapping.")

    values = {}
    for key, definition in heat_params.items():
        if not isinstance(definition, dict):
            raise ValueError(
                f"Heat template parameter '{key}' must be a mapping."
            )
        if 'default' in definition:
            values[key] = definition['default']

    if env_parameters is not None:
        for key, value in env_parameters.items():
            if key not in heat_params:
                raise ValueError(f"Heat env parameter '{key}' was not found.")
            values[key] = value

    parameters = heat_globals.get('parameters', [])
    if not isinstance(parameters, list):
        raise ValueError("Heat configuration 'parameters' must be a list.")

    environment_overrides = {}
    if multi_stack_environment['num_ranges'] > 1:
        environment_overrides = {
            'domain_name': multi_stack_environment['domain_name'],
            'domain_netbios_name': multi_stack_environment['domain_netbios_name'],
            'cs_number': multi_stack_environment['cs_number'],
            'org_name': multi_stack_environment['org_name'],
            'range_number': multi_stack_environment['range_number'],
            'csToken': multi_stack_environment['csToken'],
        }

    for parameter in parameters:
        if not isinstance(parameter, dict):
            raise ValueError(
                "Each Heat configuration parameter must be a mapping."
            )
        for key, value in parameter.items():
            if key not in heat_params:
                raise ValueError(f"Heat parameter '{key}' was not found.")
            if key in environment_overrides:
                value = environment_overrides[key]
                if value is None:
                    raise ValueError(
                        f"Environment variable '{key}' is required when "
                        "'num_ranges' is greater than 1."
                    )
            values[key] = value
            msg_format.info_msg(
                f"Updated parameter '{key}' with value '{value}'.",
                endpoint,
                debug
            )

    msg_format.success_msg(f"Updated heat parameters.",
                           endpoint)

    return values
