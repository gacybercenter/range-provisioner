"""_summary_:
This function connects to an OpenStack cloud, loads a Heat template file,
and replaces the resource IDs in the template with the actual resource IDs.
The replacement is based on the specified connection and the names of the
resources to be processed. If no stack names are provided, all stacks will
be processed.
"""
import yaml
from openstack import connection
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def get_ids(conn: connection, heat_template: object, names: list, debug: bool):
    """
    Retrieves resource IDs from OpenStack for the specified stack names.

    Parameters:
        - conn (connection): The connection object to filter the stacks.
        - heat_template (object): The Heat template to modify.
        - names (list): The names of the resource. If blank, all stacks
        in the specified cloud will be processed.
        - debug (bool): Whether to print debug messages.

    Returns:
        - heat_template (dict): The modified Heat template.
    """
    # Gets the names of all stacks in the specified cloud if none are provided
    if not names:
        general_msg("No stacks provided, getting IDs from all stacks...")
        stacks = conn.orchestration.stacks()
        for stack in stacks:
            name = stack.name
            stackinfo = conn.orchestration.find_stack(name)
            if stackinfo is not None:
                names.append(name)

    # Make instances of resourcename_id in Heat template containing resource IDs
    for name in names:
        info_msg(f"Getting IDs from {name}", debug)
        for resource in conn.orchestration.resources(name):
            resource_name = resource.logical_resource_id
            resource_id = resource.physical_resource_id
            if "network" in resource_name or "subnet" in resource_name:
                heat_template["parameters"][resource_name +
                                            '_id'] = resource_id

    success_msg("Retrieved IDs from OpenStack")
    return heat_template


def modify_yaml(template_path: str, heat_template: object):
    """
    Modifies the Heat template by writing it back to the file.

    Parameters:
        - template_path (str): The path to the Heat template file.
        - heat_template (object): The modififications to the Heat template.

    Returns:
        None
    """
    try:
        with open(template_path, 'w', encoding='utf-8') as template_file:
            yaml.dump(
                heat_template,
                template_file,
                encoding='utf-8',
                default_flow_style=False,
                sort_keys=True
            )
        success_msg(f"Wrote to {template_path}")

    except FileNotFoundError:
        error_msg(f"\'{template_path}\' was not found")


def replace_resource_ids(conn: connection, template_path: str, names: list, debug: bool = False):
    """
    Replaces resource IDs in a Heat template with actual resource IDs.

    Parameters:
        - conn (connection): The connection object to filter the stacks.
        - template_path (str): The path to the Heat template file.
        - names (list): The names of the resource. If blank, all stacks
        in the specified cloud will be processed.

    Returns:
        - heat_template (dict): The modified Heat template.
    """
    try:
        general_msg(f"Reading {template_path}")
        with open(template_path, 'r', encoding='utf-8') as template_file:
            heat_template = yaml.safe_load(template_file)

        general_msg("Getting network resource IDs from OpenStack...")
        heat_template = get_ids(conn, heat_template, names, debug)

        general_msg(f"Writing network resource IDs to {template_path}")
        modify_yaml(template_path, heat_template)

        return heat_template

    except Exception as error:
        error_msg(error)
        return None
