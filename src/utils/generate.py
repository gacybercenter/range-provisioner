import secrets
import string
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))

def generate_names(ranges, prefix, suffix):
    """Generate a list of names with a prefix and a range of numbers"""
    return [f"{prefix}{suffix}{i}" for i in range(ranges)]


def instances(ranges, users, range_name, instance_name, debug):
    """Create instance list"""
    try:
        instance_names = [f"{name}.{instance_name}.{u}" for name in generate_names(
            ranges, range_name, '-') for u in range(users)]
        general_msg(f"Generating instance list for {range_name}")
        for instance in instance_names:
            general_msg(f"Instance Generated: {instance}")
        return instance_names
    except Exception as e:
        error_msg(e)
        return None


def users(ranges, users, range_name, user_name, secure, debug):
    """Create user list"""
    try:
        user_names = [f"{name}.{user_name}.{u}" for name in generate_names(
            ranges, range_name, '-') for u in range(users)]
        general_msg(f"Generating user list")
        if secure:
            users_list = {user: {'password': generate_password()} for user in user_names}
        else:
            users_list = {user: {'password': range_name} for user in user_names}
        for u, p in users_list.items():
            if debug:
                info_msg(f"username: {u} {p['password']}", debug)
            else:
                general_msg(f"User Generated: {u}")
        return users_list
    except Exception as e:
        error_msg(e)
        return None
