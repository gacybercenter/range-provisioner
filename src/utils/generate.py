import secrets
import string
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def generate_password():
    """
    Generate a random password consisting of 16 characters.

    Returns:
        str: The generated password.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))


def generate_names(ranges, prefix):
    """Generate a list of names with a prefix and a range of numbers"""
    return [f"{prefix}{i+1}" for i in range(ranges)]


def generate_instance_names(params, guac_params, debug):
    """Generate a list of instance names based on given ranges and names"""
    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    user_name = params.get('user_name')
    range_name = params.get('range_name')

    try:
        general_msg(f"Generating instance names for {range_name}")
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

def generate_user_names(params, guac_params, debug):
    """Create user list"""
    num_ranges = params.get('num_ranges')
    num_users = params.get('num_users')
    range_name = params.get('range_name')
    user_name = params.get('user_name')
    secure = guac_params.get('secure')

    try:
        general_msg(f"Generating user names for {range_name}")
        user_names = [f"{name}.{user_name}.{u+1}" for name in generate_names(
            num_ranges, range_name) for u in range(num_users)]
        users_list = {user:  generate_password() if secure else {
            user: range_name} for user in user_names}
        info_msg(users_list, debug)

        return users_list
    except Exception as error:
        error_msg(error)
        return None


def generate_group_names (params, guac_params, debug):
    """Generate a list of group names based on given ranges"""
    num_ranges = params.get('num_ranges')
    range_name = params.get('range_name')

    try:
        general_msg(f"Generating child group names for {range_name}")
        instance_names = generate_names(num_ranges, range_name)
        info_msg(instance_names, debug)
        return instance_names
    except Exception as error:
        error_msg(error)
        return None
