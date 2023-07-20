"""_summary_:
This function connects to an OpenStack cloud, loads a Heat template file,
and replaces the resource IDs in the template with the actual resource IDs.
The replacement is based on the specified connection and the stacks of the
resources to be processed. If no stacks are provided, all stacks will
be processed.
"""
import json
import yaml
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def update_env(conn,
               global_dict: object,
               replace: bool = False,
               debug: bool = False):
    """
    Updates the env.yaml file with up to date resource IDs.

    Parameters:
        - conn (connection): The connection object.
        - global_dict (object): The global dictionary object.
        - replace (bool, optional): Flag indicating whether to replace existing
        stacks. Defaults to False.
        - debug (bool, optional): Flag indicating whether to enable debug mode.
        Defaults to False.

    Returns:
        None
    """
    try:
        stacks = global_dict.heat['env']
        general_msg("Found env stacks in the globals dictionary")
        info_msg(json.dumps(stacks, indent=4), debug)
    except KeyError:
        general_msg("Could not find env stacks in the globals dictionary")
        stacks = []

    try:
        env_path = global_dict.heat['template_dir']+"/env.yaml"
        env_params = read_yaml(env_path)
        env_params = get_ids(conn,
                             env_params,
                             stacks,
                             replace,
                             debug)
        write_yaml(env_path, env_params)
    except KeyError:
        env_path = None


def update_ids(conn,
               params: list,
               stacks: list,
               replace: bool = False,
               debug: bool = False):
    """
    Update the IDs in the parameters.

    Parameters:
        - conn (connection): The database connection.
        - params (list): The list of parameters.
        - stacks (list): The list of stacks.
        - replace (bool, optional): Whether to make new IDs or not.
        Defaults to False.
        - debug (bool, optional): Whether to enable debugging or not.
        Defaults to False.

    Returns:
        list: The updated list of parameters.

    """
    modified_params = []
    for param in params:
        modified_params.append(
            get_ids(conn,
                    param,
                    stacks,
                    replace,
                    debug)
        )
    success_msg(f"Updated {len(modified_params)} params dictionaries")
    return modified_params


def compare_dictionaries(dict1, dict2):
    """
    Compare two dictionaries and return a list of different entries.

    Parameters:
        dict1 (dict): The first dictionary to compare.
        dict2 (dict): The second dictionary to compare.
        debug (bool): Whether to print debug information.

    Returns:
        list: A list of tuples containing the keys and different values between the dictionaries.
    """
    different_entries = []
    for key in dict1.keys():
        if key in dict2 and dict1[key] != dict2[key]:
            different_entries.append((key, dict1[key], dict2[key]))
    return different_entries


def get_ids(conn, params, stack_list, replace=False, debug=False):
    """
    Retrieves resource IDs from OpenStack.

    Parameters:
    - conn: The connection object to the OpenStack API.
    - params: The parameters to be modified.
    - stacks: The stacks of the stacks to retrieve IDs from. If none are
    provided, IDs will be retrieved from all stacks.
    - replace: A boolean indicating whether to replace existing parameter
    values with the retrieved IDs.
    - debug: A boolean indicating whether to enable debug mode.

    Returns:
    - modified_params: The modified parameters with the retrieved IDs.
    """
    # Gets the stacks of all stacks in the specified cloud if none are provided
    if not stack_list:
        general_msg("No stacks provided, getting resource IDs from all stacks")
        stacks = conn.orchestration.stacks()
        for stack in stacks:
            name = stack.name
            stackinfo = conn.orchestration.find_stack(name)
            if stackinfo is not None:
                stack_list.append(name)

    # Make instances of resourcename_id in Heat template containing resource IDs
    modified_params = params.copy()
    if modified_params.get('parameters') is None:
        modified_params['parameters'] = {}

    general_msg("Getting resource IDs from OpenStack")
    for stack in stack_list:
        info_msg(f"Getting IDs from {stack}", debug)
        for resource in conn.orchestration.resources(stack):
            resource_name = resource.logical_resource_id + '_id'
            resource_id = resource.physical_resource_id
            if modified_params['parameters'].get(resource_name) is not None:
                modified_params['parameters'][resource_name] = resource_id
            if replace:
                modified_params['parameters'][resource_name] = resource_id

    info_msg(
        f"Difference: {json.dumps(compare_dictionaries(params, modified_params))}",
        debug
    )

    success_msg("Retrieved IDs from OpenStack")
    return modified_params


def read_yaml(template_path: str):
    """
    Reads a YAML file and returns its contents as a Python object.

    Parameters:
        - template_path (str): The path to the YAML file.

    Returns:
        - (object): The contents of the YAML file as a Python object.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    general_msg(f"Reading file \'{template_path}\'")
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            return yaml.safe_load(template_file)

    except FileNotFoundError:
        error_msg(f"\'{template_path}\' was not found")
        return None


def write_yaml(template_path: str, heat_template: object):
    """
    Modifies the Heat template by writing it back to the file.

    Parameters:
        - template_path (str): The path to the Heat template file.
        - heat_template (object): The modififications to the Heat template.

    Returns:
        None
    """
    try:
        general_msg(f"Writing resource IDs to {template_path}")
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
