"""
Handles the logic for generating Heat and Guacamole data
"""
import secrets
import string
from utils.msg_format import error_msg, info_msg, general_msg


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
    """Generate a list of names with a prefix and a range of numbers"""

    if ranges == 1:
        return [prefix]
    return [f"{prefix}{i+1}" for i in range(ranges)]


def generate_instance_names(params: dict,
                            debug=False):
    """Generate a list of instance names based on given ranges and names"""

    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    user_name = params.get('user_name')
    range_name = params.get('range_name')

    general_msg(f"Guacamole:  Generating instance names for {range_name}")
    try:
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

    except Exception as error:
        error_msg(error)
        return None


def generate_users(params: dict,
                   guac_params: dict,
                   debug) -> dict | None:
    """Create a user list based on given ranges"""

    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    range_name = params.get('range_name')
    user_name = params.get('user_name')
    secure = guac_params.get('secure')

    general_msg(f"Guacamole:  Generating user names for {range_name}")
    try:
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
                    'password': generate_password() if secure
                    else {user: range_name, 'instances': user},
                    'instances': [user]
                }   for user in user_names
            }
        info_msg("Guacamole:  Generated Users:\n"
                 f"{users_list}", debug)

        return users_list

    except Exception as error:
        error_msg(error)
        return None


def generate_groups(params: dict,
                    debug=False) -> list | None:
    """Generate a list of group names based on given ranges"""

    num_ranges = params.get('num_ranges')
    range_name = params.get('range_name')

    general_msg(f"Guacamole:  Generating group names for {range_name}")
    if num_ranges == 1:
        info_msg("Guacamole:  Generated Group:\n"
                 f"{range_name}", debug)
        return [range_name]

    try:
        instance_names = generate_names(num_ranges, range_name)
        info_msg("Guacamole:  Generated Groups:\n"
                 f"{instance_names}", debug)

        return instance_names

    except Exception as error:
        error_msg(error)
        return None


def format_groups(user_params: dict,
                 debug=False) -> list:
    """
    Format the users.yaml data into a list of groups.

    Parameters:
        user_params (dict): The usrs.yaml dictionary.

    Returns:
        list: The group names present in the users.yaml
    """

    groups = []

    for data in user_params.values():
        instances = data.get('instances', [])
        for instance in instances:
            group = instance.split('.')[0]
            if group not in groups:
                groups.append(group)

    general_msg("Guacamole:  Retrieved groups from users.yaml")
    info_msg(f"{groups}", debug)

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

    users = {}

    for username, data in user_params.items():
        user = {
            username: {
                'password': data['password'],
                'instances': data['instances']
            }
        }
        users.update(user)

    general_msg("Guacamole:  Retrieved users from users.yaml")
    info_msg(f"{users}", debug)

    return users
