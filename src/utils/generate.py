"""
Handles the logic for generating Heat and Guacamole data
"""
from utils import msg_format
import os

# Access environment variables
num_ranges = int(os.getenv("num_ranges", 1))
org_name = os.getenv("org_name")
range_number = os.getenv("range_number")
domain_name = os.getenv("domain_name")
domain_netbios_name = os.getenv("domain_netbios_name")
cs_number = os.getenv("cs_number")
csToken = os.getenv("csToken")

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
            f"Invalid provisioning and update flags: create={
                create}, update={update}"
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
                       debug: bool = False) -> dict:
    """
    Updates the heat parameters based on the heat globals.
    """
    
    msg_format.general_msg(f"Updating heat parameters with global values.",
                           endpoint)
    
    if heat_params:
        heat_params = {
            key: value['default']
            for key, value in heat_params.items()
            if 'default' in value
        }

    if 'parameters' in heat_globals and isinstance(heat_globals['parameters'], list):
        for parameter in heat_globals['parameters']:
            for key, value in parameter.items():
                if key not in heat_params:
                    msg_format.error_msg(
                        f"Parameter '{key}' was not found.",
                        endpoint
                    )
                    continue
                if int(num_ranges) > 1:
                    if key == 'domain_name':
                        value = domain_name
                    elif key == 'domain_netbios_name':
                        value = domain_netbios_name
                    elif key == 'cs_number':
                        value = cs_number
                    elif key == 'org_name':
                        value = org_name
                    elif key == 'range_number':
                        value = range_number
                    elif key == 'csToken':
                        value = csToken
                    heat_params[key] = value
                else:
                    heat_params[key] = value
                msg_format.info_msg(
                    f"Updated parameter '{key}' with value '{value}'.",
                    endpoint,
                    debug
                )

    msg_format.success_msg(f"Updated heat parameters.",
                           endpoint)

    return heat_params
