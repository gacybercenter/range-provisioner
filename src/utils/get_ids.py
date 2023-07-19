"""_summary_:
This function connects to an OpenStack cloud, loads a Heat template file,
and replaces the resource IDs in the template with the actual resource IDs.
The replacement is based on the specified connection and the names of the
resources to be processed. If no stack names are provided, all stacks will
be processed.
"""
import json
import yaml
from openstack import connection
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def compare_dictionaries(dict1, dict2):
    different_entries = []
    for key in dict1.keys():
        if key in dict2 and dict1[key] != dict2[key]:
            different_entries.append((key, dict1[key], dict2[key]))
    return different_entries

def get_ids(conn, params, names, replace=False, debug=False):
    try:
        general_msg("Getting resource IDs from OpenStack...")
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
        modified_params = params
        if modified_params.get('parameters') is None:
            modified_params['parameters'] = {}

        for name in names:
            info_msg(f"Getting IDs from {name}", debug)
            for resource in conn.orchestration.resources(name):
                resource_name = resource.logical_resource_id + '_id'
                resource_id = resource.physical_resource_id
                if modified_params['parameters'].get(resource_name) is not None:
                    modified_params['parameters'][resource_name] = resource_id
                if replace:
                    modified_params['parameters'][resource_name] = resource_id

        if debug:
            difference = compare_dictionaries(params, modified_params)
            if not difference:
                info_msg("No differences found", debug)
            else:
                info_msg(json.dumps(difference, indent=4), debug)

        success_msg("Retrieved IDs from OpenStack")
        return modified_params
    except Exception as error:
        error_msg(error)
        return None


def read_yaml(template_path: str):
    try:
        general_msg(f"Reading file \'{template_path}\'")
        with open(template_path, 'r', encoding='utf-8') as template_file:
            return yaml.safe_load(template_file)

    except FileNotFoundError:
        error_msg(f"\'{template_path}\' was not found")


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
