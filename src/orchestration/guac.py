import json
import orchestration.heat as heat
from utils.generate import instances, users
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def provision(conn, gconn, globals, guacamole_globals, heat_params, debug=False):
    users_list = users(globals['num_ranges'], globals['num_users'],
                               globals['range_name'], globals['user_name'], guacamole_globals['secure'], debug)
    info_msg(users_list, debug)

    instances_list = instances(globals['num_ranges'], globals['num_users'],
                               globals['range_name'], guacamole_globals['instance_mapping'], debug)
    info_msg(instances_list, debug)


    return

def deprovision(conn, globals, guacamole_globals, sec_params, debug=False):
    return


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.


def create_usernames(num_users, username):
    """Create username list"""
    new_usernames = [f'{username}.{num}' for num in range(1, num_users+1)]
    return new_usernames


def get_ostack_instances():
    """Obtain openstack instance names and public addresses"""
    instances = [
        {
            'name': instance.name,
            'address': instance.public_v4
        }
        for instance in conn.list_servers()
        ]
    return instances


def get_existing_accounts():
    """Locate existing user accounts"""
    existing_accounts = list(loads(guac_session.list_users()))
    return existing_accounts


def get_conn_group_id(conn_group_name):
    """Locate connection group id"""
    conn_groups = loads(guac_session.list_connection_groups())
    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == conn_group_name
                    and not None]
    except Exception as e:
        print(f"Guacamole ERROR:  {conn_group_name}"
              f" is missing from group list \n {e}")
    return group_id


def get_conn_id(conn_name, conn_group_id):
    """Locate connection id"""
    list_conns = loads(guac_session.list_connections())
    try:
        conn_id = ([k for k, v in list_conns.items()
                   if v.get('parentIdentifier') == conn_group_id
                   and v.get('name') == conn_name])
    except Exception as e:
        print(f"Guacamole ERROR:  {conn_name}"
              f" is missing from connection list \n {e}")
    return conn_id


def create_conn_group(conn_group_name):
    """Create connection group"""
    guac_session.create_connection_group(
        conn_group_name,
        "ORGANIZATIONAL",
        "ROOT",
        {
            'max-connections': '50',
            'max-connections-per-user': '10',
            'enable-session-affinity': ''
        }
        )
    time.sleep(2)
    print(f"Guacamole:  The connection group {conn_group_name} was created")


def delete_conn_group(conn_group_name, conn_group_id):
    """Delete connection group"""
    guac_session.delete_connection_group(conn_group_id)
    print(f"Guacamole:  The connection group {conn_group_name}"
          f" with id {conn_group_id} was deleted")


def create_user_acct(user, guac_user_password, guac_user_organization):
    """"Create user accounts"""
    guac_session.create_user(f'{user}', guac_user_password,
                             {"guac-organization": guac_user_organization})
    print(f"Guacamole:  Created User Account: {user}")


def delete_user_acct(user):
    """"Delete user accounts"""
    guac_session.delete_user(user)
    print(f'Guacamole:  Deleted User Account: {user}')


def create_user_conns(conn_action, user, instances, conn_proto,
                      conn_group_id, ostack_username, ostack_pass):
    """Create/Delete user connections"""
    for instance in instances:
        if instance['address']:
            if "ssh" in conn_proto:
                conn_name = f"{instance['name']}.ssh"
                if conn_action == "delete":
                    delete_user_conns(user, conn_name, conn_group_id)
                else:
                    guac_session.manage_connection(
                        "post", "ssh", conn_name,
                        conn_group_id, None,
                        {
                            "hostname":
                            instance['address'],
                            "port": "22",
                            "username": ostack_username,
                            "password": ostack_pass
                        },
                        {
                            "max-connections": "",
                            "max-connections-per-user": "2"
                        }
                        )
                    print(f"Guacamole:  Created connection for {instance['name']}"
                            f" ssh connection with address: {instance['address']}")
                    associate_user_conns(user, conn_name, conn_group_id)
            if "rdp" in conn_proto:
                conn_name = f"{instance['name']}.rdp"
                if conn_action == "delete":
                    delete_user_conns(user, conn_name, conn_group_id)
                else:
                    guac_session.manage_connection(
                        "post", "rdp", conn_name,
                        conn_group_id, None,
                        {
                            "hostname": instance['address'],
                            "port": "3389",
                            "username": ostack_username,
                            "password": ostack_pass,
                            "security": "any",
                            "ignore-cert": "true"
                        },
                        {
                            "max-connections": "",
                            "max-connections-per-user": "2"
                        }
                        )
                    print(f"Guacamole:  Created connection for {instance['name']}"
                            f" rdp connection with address: {instance['address']}")
                    associate_user_conns(user, conn_name, conn_group_id)


def associate_user_conns(user, conn_name, conn_group_id):
    """Associate user accounts with group_id and connections"""
    time.sleep(2)
    conn = get_conn_id(conn_name, conn_group_id)[0]
    guac_session.update_user_connection(user, conn_group_id, "add", True)
    guac_session.update_user_connection(user, conn, "add", False)
    print(f"Guacamole:  Associated {conn_name} connection for {user}")


def delete_user_conns(user, conn_name, conn_group_id):
    """Delete user connections"""
    conn_id = get_conn_id(conn_name, conn_group_id)[0]
    guac_session.delete_connection(conn_id)
    print(f"Guacamole:  Deleted associated {conn_name}"
            f" connection for {user}")
