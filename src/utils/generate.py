"""
Handles the logic for generating Heat and Guacamole data
"""
import secrets
import string
from utils.msg_format import info_msg, general_msg, error_msg


def generate_password() -> str:
    """
    Generate a random password consisting of 16 characters.

    Returns:
        str: The generated password.
    """

    alphabet = string.ascii_letters + string.digits

    return ''.join(secrets.choice(alphabet) for i in range(16))


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


def generate_instance_names(range_name: str,
                            num_ranges: int,
                            user_name: str,
                            num_users: int,
                            debug: bool=False):
    """
    Generate a list of instance names based on given ranges and names

    Args:
        params (dict): The parameters for the generation
        debug (bool): A flag indicating whether to enable debug mode.

    Returns:
        list: The generated instance names
    """

    endpoint = 'Generate'

    general_msg(f"Generating instance names for '{user_name}' in '{range_name}'",
                endpoint)

    if num_users == 1:
        instance_names = [
            f"{name}.{user_name}"
            for name in generate_names(num_ranges, range_name)
        ]
    else:
        instance_names = [
            f"{name}.{user_name}.{u+1}"
            for name in generate_names(num_ranges, range_name)
            for u in range(num_users)
        ]
    info_msg(instance_names, endpoint, debug)

    return instance_names


def generate_conns(params: dict,
                   guac_params: dict,
                   debug) -> dict | None:
    """
    Create a connection list based on given ranges
    """

    endpoint = 'Generate'

    org_name = guac_params['org_name']
    new_groups = guac_params['new_groups']
    instances = guac_params['instances']
    recording = guac_params['recording']
    sharing = guac_params['sharing']

    if sharing and sharing not in ['read', 'write']:
        error_msg(
            f"The Guacamole sharing parameter is set to '{sharing}'",
            endpoint
        )
        general_msg(
            "It must be either 'read', 'write', or 'False'",
            endpoint
        )

    general_msg("Generating connection data",
                endpoint)

    guacd_ips = {}

    # Filter instances by guacd
    for instance in instances.copy():
        if "guacd" in instance['name']:
            guacd_org = get_group_name(instance['name'])
            guacd_ips[guacd_org] = instance['hostname']
            instances.remove(instance)

    conn_objects = []

    # Process each instance
    for instance in instances:
        group = get_group_name(instance['name'])
        conn_objects.append({
            'name': instance['name'],
            'protocol': guac_params['protocol'],
            'attributes': {
                'max-connections': '1',
                'max-connections-per-user': '1',
                'guacd-hostname': guacd_ips.get(group, '')
            },
            'sharingProfiles': {
                'attributes': {},
                'name': f"{instance['name']}.{sharing}",
                'parameters': {
                    "read-only": 'true'
                } if sharing == 'read' else {}
            } if sharing else {},
            'parameters': {
                'hostname': instance['hostname'],
                'username': guac_params['username'],
                'password': guac_params['password'],
                "domain": guac_params['domain_name'],
                "port": "3389" if guac_params['protocol'] == "rdp" else "22",
                "security": "any" if guac_params['protocol'] == "rdp" else "",
                "ignore-cert": "true" if guac_params['protocol'] == "rdp" else "",
                "enable-wallpaper": "true" if guac_params['protocol'] == "rdp" else "",
                "enable-theming": "true" if guac_params['protocol'] == "rdp" else "",
                "create-recording-path": "true" if recording else "",
                "recording-name": "${GUAC_USERNAME}-${GUAC_DATE}-${GUAC_TIME}" if recording else "",
                "recording-path": "${HISTORY_PATH}/${HISTORY_UUID}" if recording else "",
            }
        })

    # Generate the create data
    if org_name == new_groups[0]:
        conn_dict = {
        'name': org_name,
        'type': 'ORGANIZATIONAL',
        'childConnections': conn_objects,
        'attributes': {
            'max-connections': '50',
            'max-connections-per-user': '10'
        }
    }
    else:
        group_map = {}
        for conn in conn_objects:
            conns = group_map.setdefault(
                get_group_name(conn['name']), []
            )
            if conn not in conns:
                conns.append(conn)

        conn_dict = {
            'name': org_name,
            'type': 'ORGANIZATIONAL',
            'childConnectionGroups': [
                {
                    'name': group,
                    'type': 'ORGANIZATIONAL',
                    'childConnections': conns,
                    'attributes': {
                        'max-connections': '50',
                        'max-connections-per-user': '10'
                    }
                }
                for group, conns in group_map.items()
            ],
            'attributes': {
                'max-connections': '50',
                'max-connections-per-user': '10'
            }
        }

    info_msg(conn_dict,
             endpoint,
             debug)

    return conn_dict


def generate_users(params: dict,
                   guac_params: dict,
                   debug: bool = False) -> dict | None:
    """Create a user list based on given ranges"""

    endpoint = 'Generate'
    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    range_name = params.get('range_name')
    users = guac_params.get('users')
    sharing = guac_params.get('sharing')
    org_name = guac_params['org_name']

    general_msg(f"Generating user data for {range_name}",
                endpoint)

    instance_names = [
        instance_name['name']
        for instance_name in guac_params['instances']
    ]

    users_list = []

    if isinstance(users, str):
        users_list.extend([
            {
                "username": username,
                "data": {}
            }
            for username in generate_instance_names(range_name,
                                                    num_ranges,
                                                    users,
                                                    num_users,
                                                    debug)
        ])

    elif isinstance(users, list):
        users_list.extend([
            {
                "username": username,
                "data": {}
            }
            for user_name in users
            for username in generate_instance_names(range_name,
                                                    num_ranges,
                                                    user_name,
                                                    num_users,
                                                    debug)
        ])

    elif isinstance(users, dict):
        users_list.extend([
            {
                "username": username,
                "data": data
            }
            for user_name, data in users.items()
            for username in generate_instance_names(range_name,
                                                    num_ranges,
                                                    user_name,
                                                    data.get('amount', num_users),
                                                    debug)
        ])

    user_dict = {}

    for user in users_list:
        instances = user['data'].get('instances', [
            user['username'],
            get_connection_name(user['username'])
        ])

        expand_instances(instances,
                         instance_names,
                         debug)

        groups = [
            get_group_name(instance)
            for instance in instances
        ] + [org_name]

        sharing_copy = user['data'].get('sharing', sharing)

        user_dict[user['username']] = {
            'password': user['data'].get('password', generate_password()),
            'permissions': {
                'connectionPermissions': instances,
                'connectionGroupPermissions': groups,
                'sharingProfilePermissions': [
                    f"{user['username']}.{sharing_copy}"
                ] if sharing_copy else [],
                'userPermissions': {
                    user['username']: ['READ']
                },
                'userGroupPermissions': user['data'].get('groups', []),
                'systemPermissions': user['data'].get('permissions', [])
            }
        }

    info_msg(user_dict,
             endpoint,
             debug)

    return user_dict


def generate_groups(params: dict,
                    debug=False) -> list | None:
    """Generate a list of group names based on given ranges"""

    num_ranges = params.get('num_ranges')
    range_name = params.get('range_name')
    endpoint = 'Generate'

    general_msg(f"Generating group names for {range_name}",
                endpoint)

    group_names = generate_names(num_ranges,
                                 range_name)
    info_msg(group_names,
             endpoint,
             debug)

    return group_names


def format_groups(user_params: dict,
                  debug=False) -> list:
    """
    Format the users.yaml data into a list of groups.

    Parameters:
        user_params (dict): The users.yaml dictionary.

    Returns:
        list: The group names present in the users.yaml
    """

    endpoint = 'Generate'
    groups = set()

    for data in user_params.values():
        instances = data.get('instances', [])
        for instance in instances:
            group = get_group_name(instance)
            groups.add(group)

    groups = list(groups)

    general_msg("Retrieved groups from users.yaml",
                endpoint)
    info_msg(groups,
             endpoint,
             debug)

    return groups


def format_users(user_params: dict,
                 guac_params: dict,
                 debug=False) -> dict:
    """
    Format the users.yaml data into a dictionary of user objects.

    Parameters:
        user_params (dict): The usrs.yaml dictionary.

    Returns:
        dict: The formated users dictionary.
    """

    endpoint = 'Generate'
    org_name = guac_params['org_name']
    instance_names = [
        instance_name['name']
        for instance_name in guac_params['instances']
    ]
    users = {}

    for username, data in user_params.items():
        sharing = guac_params.get('sharing')
        sharing = data.get('sharing', sharing)
        if sharing and sharing not in ['read', 'write']:
            error_msg(
                f"The Guacamole sharing parameter is set to '{sharing}'",
                endpoint
            )
            general_msg(
                "It must be either 'read', 'write'",
                endpoint
            )
            sharing = None

        instances = data.get('instances', [])

        expand_instances(instances,
                         instance_names,
                         debug)

        user = {
            username: {
                'username': username,
                'password': data['password'],
                'attributes': {'guac-organization': org_name},
                'permissions': {
                    'connectionPermissions': data.get('instances', []),
                    'connectionGroupPermissions': set(
                        get_group_name(instance)
                        for instance in [org_name] + data.get('instances')
                    ),
                    'sharingProfilePermissions': [
                        f"{instance}.{sharing}"
                        for instance in data.get('instances')
                    ] if sharing else [],
                    'userPermissions': {
                        username: ['READ']
                    },
                    'userGroupPermissions': data.get('groups', {}),
                    'systemPermissions': data.get('permissions', [])
                }
            }
        }
        users.update(user)

    general_msg("Retrieved users from users.yaml",
                endpoint)
    info_msg(users,
             endpoint,
             debug)

    return users


def get_group_name(name: str) -> str:
    """
    Generate a group name based on the given name.
    """

    parts = name.split('.')
    if len(parts) == 1:
        return parts[0]

    if parts[1].isdigit():
        return f"{parts[0]}.{parts[1]}"

    return parts[0]

def get_connection_name(name: str) -> str:
    """
    Generate a connection name based on the given name.
    """

    parts = name.split('.')
    if len(parts) == 1:
        return parts[0]

    if parts[-1].isdigit():
        return f"{parts[-2]}.{parts[-1]}"

    return parts[-1]

def expand_instances(instances: list,
                     instance_names: dict,
                     debug: bool = False) -> list:
    """
    Expand the instances list based on the heat instances list.
    """

    endpoint = 'Generate'

    # If a user has an instance not in the heat_instances list, pattern match
    for instance in instances:
        if instance.endswith('*'):
            instance_pattern = instance.removesuffix('*')
            heat_instances = [
                heat_instance
                for heat_instance in instance_names
                if instance_pattern in heat_instance
            ]
            info_msg(
                f"Turned '{instance}' into {heat_instances}",
                endpoint,
                debug
            )
            instances.remove(instance)
            instances.extend(heat_instances)
        elif instance not in instance_names:
            error_msg(
                f"The instance '{instance}' does not exist",
                endpoint
            )
            instances.remove(instance)
