"""
Handles the logic for generating Heat and Guacamole data
"""
import secrets
import string
from utils.msg_format import info_msg, general_msg


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

    return [f"{prefix}{i+1}" for i in range(ranges)]


def generate_instance_names(params: dict,
                            debug=False):
    """
    Generate a list of instance names based on given ranges and names

    Args:
        params (dict): The parameters for the generation
        debug (bool): A flag indicating whether to enable debug mode.

    Returns:
        list: The generated instance names
    """

    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    user_name = params.get('user_name')
    range_name = params.get('range_name')
    endpoint = 'Generate'

    general_msg(f"Generating instance names for {range_name}",
                endpoint)

    if num_users == 1:
        instance_names = [f"{range_name}.{user_name}"]
    else:
        instance_names = [
            f"{name}.{user_name}.{u+1}"
            for name in generate_names(num_ranges, range_name)
            for u in range(num_users)
        ]
    info_msg(instance_names, debug)

    return instance_names


def generate_users(params: dict,
                   debug) -> dict | None:
    """Create a user list based on given ranges"""

    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    range_name = params.get('range_name')
    user_name = params.get('user_name')
    endpoint = 'Generate'

    general_msg(f"Generating user names for {range_name}",
                endpoint)

    if num_users == 1:
        user_names = [f"{range_name}.{user_name}"]
    else:
        user_names = [
            f"{name}.{user_name}.{u+1}"
            for name in generate_names(num_ranges, range_name)
            for u in range(num_users)
        ]
    users_list = {
        user:
            {
                'password': generate_password(),
                'instances': [user]
            } for user in user_names
    }
    info_msg(users_list,
             endpoint,
             debug)

    return users_list


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
        user_params (dict): The usrs.yaml dictionary.

    Returns:
        list: The group names present in the users.yaml
    """

    endpoint = 'Generate'
    groups = []

    for data in user_params.values():
        instances = data.get('instances', [])
        for instance in instances:
            group = instance.split('.')[0]
            if group not in groups:
                groups.append(group)

    general_msg("Retrieved groups from users.yaml",
                endpoint)
    info_msg(groups,
             endpoint,
             debug)

    return groups


def format_users(user_params: dict,
                 debug=False) -> dict:
    """
    Format the users.yaml data into a dictionary of user objects.

    Parameters:
        user_params (dict): The usrs.yaml dictionary.

    Returns:
        dict: The formated users dictionary.
    """

    endpoint = 'Generate'
    users = {}

    for username, data in user_params.items():
        user = {
            username: {
                'password': data['password'],
                'instances': data['instances']
            }
        }
        users.update(user)

    general_msg("Retrieved users from users.yaml",
                endpoint)
    info_msg(users,
             endpoint,
             debug)

    return users
