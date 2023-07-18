"""_summary_:
This function connects to an OpenStack cloud, loads a Heat template file,
and replaces the resource IDs in the template with the actual resource IDs.
The replacement is based on the specified cloud name and the names of the
resources to be processed. If no stack names are provided, all stacks will
be processed.
"""
import openstack
import yaml


def replace_resource_ids(template_path: str, cloud: str, names: list):
    """
    Replaces resource IDs in a Heat template with actual resource IDs.

    Parameters:
        - template_path (str): The path to the Heat template file.
        - cloud (str): The cloud name to filter the stacks.
        - names (list): The names of the resource. If blank, all stacks
        in the specified cloud will be processed.

    Returns:
        - heat_template (dict): The modified Heat template.
    """
    # Establish connection with OpenStack
    conn = openstack.connect(cloud=cloud)
    project_id = conn.config.get_auth_args()['project_id']
    print(
        f"\033[92mOpened connection with OpenStack cloud: {cloud}\n\033[0m"
        f"\033[93mProject ID: {project_id}\033[0m"
    )

    # Load Heat template
    with open(template_path, 'r', encoding='utf-8') as template_file:
        heat_template = yaml.safe_load(template_file)

    # Gets the names of all stacks in the specified cloud if none are provided
    if names == []:
        print(
            f"\033[94mNo stacks provided, using all stacks in {cloud}\033[0m")
        stacks = conn.orchestration.stacks(project_id=project_id)
        for name in stacks:
            print(name.name)
            stackinfo = conn.orchestration.find_stack(name.name)
            if stackinfo is not None: 
                print(name.name)
                names.append(name.name)

    #Make instances of resourcename_id in Heat template containing resource IDs
    for name in names:
        print(f"Getting IDs from: \033[33m{name}\033[0m")
        for resource in conn.orchestration.resources(name):
            resource_name = resource.logical_resource_id
            resource_id = resource.physical_resource_id
            if "network" in resource_name or "subnet" in resource_name:
                heat_template["parameters"][resource_name +
                                            '_id'] = resource_id

    # Close connection with OpenStack
    conn.close()
    print(f"\033[92mClosed connection with OpenStack cloud: {cloud}\033[0m")

    # # Write modified template back to the file
    with open(template_path, 'w', encoding='utf-8') as template_file:
        yaml.dump(
            heat_template,
            template_file,
            encoding='utf-8',
            default_flow_style=False,
            sort_keys=True
        )

    print(f"Wrote to: \033[35m{template_path}\033[0m")
    return heat_template


HEAT_TEMPLATE_PATH = '../templates/env.yaml'
CLOUD = 'testing'
STACK_NAMES = []

modified_template = replace_resource_ids(
    HEAT_TEMPLATE_PATH, CLOUD, STACK_NAMES)