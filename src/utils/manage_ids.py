"""_summary_:
This function connects to an OpenStack cloud, loads a Heat template file,
and replaces the resource IDs in the template with the actual resource IDs.
The replacement is based on the specified connection and the stacks of the
resources to be processed. If no stacks are provided, all stacks will
be processed.
"""
import yaml
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


<<<<<<< HEAD
def update_env(conn: object,
               globals_dict: object,
               make_entries: bool = False,
               debug: bool = False):
    """
    Updates the env.yaml file with up to date resource IDs.

    Parameters:
        - conn (object): The connection object.
        - globals_dict (object): The global dictionary object.
        - make_entries (bool, optional): Flag indicating whether to make new
        stacks. Defaults to False.

    Returns:
        (None)
    """
    general_msg("Updating network and subnet IDs in the env.yaml file")
    stacks = get_env_stacks(globals_dict)
    env_path = get_env_path(globals_dict)

    if env_path:
        env_params = read_yaml(env_path)
        env_params = get_ids(conn,
                             env_params,
                             stacks,
                             make_entries,
                             debug)
        write_yaml(env_path, env_params)
    return env_params


def get_env_stacks(globals_dict: dict) -> list:
    """
    Retrieve the environment stacks from the given globals dictionary.

    Parameters:
        globals_dict (dict): A dictionary containing global variables.

    Returns:
        (list): A list of environment stacks.

    Raises:
        KeyError: If the 'env' key is not present in the globals dictionary.
    """
    try:
        stacks = globals_dict.heat['env']
    except KeyError:
        stacks = []
    return stacks


def get_env_path(globals_dict: dict) -> str:
    """
    Given a dictionary of global variables, this function retrieves the path to the
    environment YAML file. 

    Parameters:
        globals_dict (dict): A dictionary containing the global variables.

    Returns:
        (str or None): The path to the environment YAML file if it exists, otherwise None.
    """
    try:
        env_path = globals_dict.heat['template_dir'] + "/env.yaml"
    except KeyError:
        error_msg("Could not resolve: 'globals_dict.heat['template_dir']'")
        env_path = None
    return env_path


<<<<<<< HEAD
def manage_params(heat_template: object) -> object:
    """
    Generates a new heat template by managing the parameters.

    Args:
        heat_template (object): The original heat template. If None, an empty heat
        template will be initialized.

    Returns:
        (object): The updated heat template with managed parameters.
    """
    if heat_template is None:
        heat_template = {"parameters": {}}
        general_msg("The heat template is empty, initializing it for you...")
    elif heat_template.get("parameters") is None:
        heat_template['parameters'] = {}
        general_msg("Adding a parameters key to the heat template...")
    return heat_template


def update_ids(conn: object,
=======
def update_ids(conn,
>>>>>>> 5035f53 (fix: ci trigger validation)
               params: list,
               stacks: list,
               make_entries: bool = False,
               debug: bool = False) -> list:
    """
    Update the IDs in the parameters.

    Parameters:
        - conn (connection): The connection object.
        - params (list): The list of parameters.
        - stacks (list): The list of stacks.
        - make_entries (bool, optional): Whether to make new IDs or not.
        Defaults to False.
        - debug (bool, optional): Whether to enable debugging or not.
        Defaults to False.

    Returns:
        (list): The updated list of parameters.

    """
    general_msg("Updating network and subnet IDs in param dictionaries")
    modified_params = [
        get_ids(conn,
                param,
                stacks,
                make_entries,
                debug)
        for param in params
    ]

    general_msg(f"Updated {len(modified_params)} params dictionaries")
    return modified_params


def get_ids(conn: object,
            parameters: dict,
            stack_names: list,
            make_entries: bool = False,
            debug: bool = False) -> object:
    """
    Retrieves the resource IDs from the specified OpenStack stacks.

    Args:
        - conn (object): The connection object.
        - parameters (dict): The parameters.
        - stack_names (list): The stack names.
        - make_entries (bool, optional): Whether to make new IDs or not.
        Defaults to False.
        - debug (bool, optional): Whether to enable debugging or not.
        Defaults to False.

    Returns:
        (object): The modified parameters.
    """
    if make_entries:
        parameters = manage_params(parameters)

    project_id = conn.current_project_id
    info_msg(f"Current project ID: {project_id}", debug)

<<<<<<< HEAD
    if not stack_names:
        general_msg("No stacks provided, fetching all stacks...")
        stacks = conn.orchestration.stacks(project_id=project_id)
=======

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
>>>>>>> 5035f53 (fix: ci trigger validation)
        for stack in stacks:
            if conn.orchestration.find_stack(stack.name) is not None:
                stack_names.append(stack.name)

    modified_params = parameters.copy()

    general_msg(f"Getting IDs from: {stack_names}")
    for stack_name in stack_names:
        for resource in conn.orchestration.resources(stack_name):
            resource_id = resource.physical_resource_id
            resource_name = resource.logical_resource_id

            if "network" in resource_name or "subnet" in resource_name:
                try:
                    new_resource_name = conn.network.find_network(
                        resource_id).name
                except AttributeError:
                    pass
                try:
                    new_resource_name = conn.network.find_subnet(
                        resource_id).name
                except AttributeError:
                    pass

                if new_resource_name:
                    resource_name = update_resource_name(new_resource_name,
                                                         stack_name)
                replace_resource_id(modified_params,
                                    resource_name,
                                    resource_id,
                                    make_entries,
                                    debug)
    success_msg("Retrieved IDs from OpenStack")
    return modified_params


def update_resource_name(resource_name: str,
                         stack_name: str) -> str:
    """
    Update the resource name by removing the prefix that matches the given name.

    Parameters:
        - resource_name (str): The original resource name.
        - stack_name (str): The name used to identify the prefix.

    Returns:
        (str): The updated resource name without the prefix.
    """
    new_resource_name = resource_name.replace(
        f"{stack_name}-", "").replace(
            f"{stack_name}.", "")

    return new_resource_name


def replace_resource_id(data: dict,
                        resource_name: str,
                        resource_id: str,
                        make_entries: bool = False,
                        debug: bool = False) -> None:
    """
    Replaces the resource ID in the given data with the provided resource ID.

    Parameters:
        - data (dict or list): The data structure in which the resource ID needs to be replaced.
        - resource_name (str): The name of the resource.
        - resource_id (str): The new resource ID.
        - make_entries (bool): Whether to make new IDs or not.
        - debug (bool): Specifies whether debug messages should be printed or not.

    Returns:
        (None)
    """
    if make_entries and resource_name:
        if not data["parameters"].get(f"{resource_name}_id"):
            info_msg(f"Adding: '{resource_name}_id': "
                     f"'{resource_id}'", debug)
        elif data["parameters"][f"{resource_name}_id"] == resource_id:
            info_msg(f"Unchanged: '{resource_name}_id': "
                     f"'{resource_id}' ", debug)
        elif data["parameters"][f"{resource_name}_id"] != resource_id:
            info_msg(f"Updating: '{resource_name}_id': "
                     f"'{data['parameters'][f'{resource_name}_id']}' to "
                     f"'{resource_id}'", debug)
        data["parameters"][f"{resource_name}_id"] = resource_id
    else:
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if isinstance(value, dict):
                    replace_resource_id(value,
                                        resource_name,
                                        resource_id,
                                        False,
                                        debug)
                elif key == f"{resource_name}_id" and data[key] == resource_id:
                    info_msg(f"Unchanged: '{resource_name}_id': "
                             f"'{resource_id}'", debug)
                elif key == f"{resource_name}_id" and data[key] != resource_id:
                    info_msg(f"Updating: '{resource_name}_id': "
                             f"'{data[key]}' to "
                             f"'{resource_id}'", debug)
                    data[key] = resource_id
        elif isinstance(data, list):
            for item in data:
                replace_resource_id(item,
                                    resource_name,
                                    resource_id,
                                    False,
                                    debug)


def read_yaml(template_path: str,
              encoding: str = 'utf-8') -> object:
    """
    Reads a YAML file and returns its contents as a Python object.

    Parameters:
        template_path (str): The path to the YAML file.

    Returns:
        (object): The contents of the YAML file as a Python object.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    general_msg(f"Reading file \'{template_path}\'")
    try:
        with open(template_path, 'r', encoding=encoding) as template_file:
            heat_template = yaml.safe_load(template_file)
    except FileNotFoundError:
        general_msg(
            f"Could not find \'{template_path}\', making it for you...")
        with open(template_path, 'w', encoding=encoding) as template_file:
            heat_template = {"parameters": {}}
            yaml.dump(heat_template, template_file, encoding=encoding)
    return heat_template


def write_yaml(template_path: str,
               heat_template: object,
               encoding: str = 'utf-8') -> None:
    """
    Modifies the Heat template by writing it back to the file.

    Parameters:
        - template_path (str): The path to the Heat template file.
        - heat_template (object): The modififications to the Heat template.

    Returns:
        (None)
    """
    try:
        general_msg(f"Writing resource IDs to {template_path}")
        with open(template_path, 'w', encoding=encoding) as template_file:
            yaml.dump(
                heat_template,
                template_file,
                encoding=encoding,
                default_flow_style=False,
                sort_keys=True
            )
        success_msg(f"Wrote to {template_path}")

    except FileNotFoundError:
        error_msg(f"\'{template_path}\' was not found")
