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


def generate_names(ranges, prefix,):
    """Generate a list of names with a prefix and a range of numbers"""
    return [f"{prefix}{i}" for i in range(ranges)]


def generate_instance_names(ranges, range_users, range_name, instance_name, debug):
    """
    Generate a list of instance names based on given ranges and names.
    """
    try:
        general_msg(f"Generating Instance Names for {range_name}")
        instance_names = [
            f"{name}.{instance_name}.{u}"
            for name in generate_names(ranges, range_name)
            for u in range(range_users)
        ]
        info_msg(instance_names, debug)
        return instance_names
    except Exception as e:
        error_msg(e)
        return None


def create_user_list(ranges, range_users, range_name, user_name, secure, debug):
    """Create user list"""
    try:
        general_msg(f"Creating User List for {range_name}")
        user_names = [f"{name}.{user_name}.{u}" for name in generate_names(
            ranges, range_name) for u in range(range_users)]
        users_list = {user: {'password': generate_password()} if secure else {
            user: {'password': range_name}} for user in user_names}
        info_msg(users_list, debug)

        # for user, password in users_list.items():
        #     general_msg(f"User Generated: {user}")

        return users_list
    except Exception as e:
        error_msg(e)
        return None
