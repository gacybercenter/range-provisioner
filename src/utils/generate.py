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
    conn_dict = {
        'name': org_name,
        'type': 'ORGANIZATIONAL',
        'childConnectionGroups': [
            {
                'name': group,
                'type': 'ORGANIZATIONAL',
                'childConnections': [
                    conn
                    for conn in conn_objects
                    if get_group_name(conn['name']) == group
                ],
                'attributes': {
                    'max-connections': '50',
                    'max-connections-per-user': '10'
                }
            }
            for group in new_groups
        ],
        'attributes': {
            'max-connections': '50',
            'max-connections-per-user': '10'
        }
    } if org_name != new_groups[0] else {
        'name': org_name,
        'type': 'ORGANIZATIONAL',
        'childConnections': conn_objects,
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
                   debug) -> dict | None:
    """Create a user list based on given ranges"""

    endpoint = 'Generate'
    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    range_name = params.get('range_name')
    user_name = params.get('user_name') # For backwards compatibility
    user_names = guac_params.get('user_names')
    sharing = guac_params.get('sharing')
    org_name = guac_params['org_name']

    general_msg(f"Generating user data for {range_name}",
                endpoint)

    if not user_names:  # For backwards compatibility
        user_names = [user_name]

    users = []

    if isinstance(user_names, str):
        user_names = [user_names]

    if isinstance(user_names, list):
        users.extend([
            {
                "username": f"{name}.{user_name}.{u+1}",
                "data": {}
            }
            if num_users > 1 else
            {
                "username": f"{name}.{user_name}",
                "data": {}
            }
            for user_name in user_names
            for name in generate_names(num_ranges, range_name)
            for u in range(num_users)
        ])

    elif isinstance(user_names, dict):
        users.extend([
                {
                    "username": f"{name}.{user_name}.{u+1}",
                    "data": data
                }
                 if num_users > 1 else
                {
                    "username": f"{name}.{user_name}",
                    "data": data
                }
            for user_name, data in user_names.items()
            for name in generate_names(num_ranges, range_name)
            for u in range(num_users)
        ])

    user_dict = {
        user['username']:
            {
                'password': user['data'].get('password', generate_password()),
                'permissions': {
                    'connectionPermissions': user['data'].get(
                        'instances', [
                            user['username'],
                            get_connection_name(user['username'])
                        ]
                    ),
                    'connectionGroupPermissions': [
                        org_name,
                        get_group_name(user['username'])
                    ],
                    'sharingProfilePermissions': [
                        f"{user['username']}.{sharing}"
                    ] if sharing else [],
                    'userPermissions': {
                        user['username']: ['READ']
                    },
                    'userGroupPermissions': user['data'].get('groups', []),
                    'systemPermissions': user['data'].get('permissions', [])
                }
            } for user in users
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
    groups = []

    for data in user_params.values():
        instances = data.get('instances', [])
        for instance in instances:
            group = instance.split('.')
            if group and group[0] not in groups:
                groups.append(group[0])

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

        # If a user has an instance not in the heat_instances list, pattern match
        for instance in data.get('instances', []):
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
                data['instances'].remove(instance)
                data['instances'].extend(heat_instances)
            elif instance not in instance_names:
                error_msg(
                    f"The instance '{instance}' does not exist",
                    endpoint
                )
                data['instances'].remove(instance)


        user = {
            username: {
                'username': username,
                'password': data['password'],
                'attributes': {'guac-organization': org_name},
                'permissions': {
                    'connectionPermissions': data.get('instances', []),
                    'connectionGroupPermissions': set(
                        instance.split('.')[0]
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
        return parts

    if parts[-1].isdigit():
        del parts[-1]
        return '.'.join(parts)

    return parts
