"""
Author: Marcus Corulli
Description: Provision and Deprovision Guacamole
Date: 08/23/2023
Version: 1.0
"""
import json
import time
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(gconn,
              guac_params,
              debug=False):
    """Provision Guacamole connections and users"""

    # Create connection group
    manage_connection_group(gconn,
                            guac_params,
                            debug)

    # Create user accounts
    manage_users(gconn,
                 guac_params,
                 debug)

    success_msg("Provisioned Guacamole")
    return True


def deprovision(gconn,
                guac_params,
                debug=False):

    """Deprovision Guacamole connections and users"""

    # Create connection group
    manage_connection_group(gconn,
                            guac_params,
                            debug)

    # Create user accounts
    manage_users(gconn,
                 guac_params,
                 debug)

    success_msg("Deprovisioned Guacamole")
    return True

#    # Create user accounts
#     for guac_user in user_names:
#         if guac_user not in existing_accounts:
#             error_msg("Guacamole ERROR:  Can't delete user account,"
#                       f" {guac_user} doesn't exist")
#         else:
#             # Delete user account
#             general_msg(f"delete_user_acct: {gconn}, {guac_user}")
#             # delete_user_acct(gconn,
#             #                  guac_user,
#             #                  debug)
#             existing_accounts.remove(guac_user)

#             # Delete user connections
#             general_msg(
#                 f"delete_user_conns: {guac_user}, {conn_group_name}, {conn_group_id}")
#             # delete_user_conns(guac_user,
#             #                   conn_group_name,
#             #                   conn_group_id,
#             #                   debug)

#     # Delete connection group
#     if conn_group_id is None:
#         error_msg(f"Guacamole ERROR:  Can't delete connection group,"
#                   f" {conn_group_name} doesn't exist")
#     else:
#         general_msg(
#             f"delete_conn_group: {gconn}, {conn_group_name}, {conn_group_id}")
#         # delete_conn_group(gconn,
#         #                   conn_group_name,
#         #                   conn_group_id,
#         #                   debug)
#     success_msg("Deprovisioned Guacamole")
#     return True

# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

# TODO(MCcrusader): Yeah, What he said. ^


def manage_connection_group(gconn, guac_params, debug=False):
    """Provision container and upload assets"""

    conn_group_name = guac_params.get('conn_group_name')
    conn_group_id = guac_params.get('conn_group_id')

    # Check if connection group exists
    if conn_group_id:
        general_msg(
            f"Guacamole:  Found connection group: {conn_group_name}, ID: {conn_group_id}")
    else:
        general_msg(
            f"Guacamole:  Could not find {conn_group_name}'s connection group. Creating one.")
        # general_msg(
        #     f"create_conn_group: {gconn}, {conn_group_name}, {conn_group_id}")
        create_conn_group(gconn,
                          conn_group_name,
                          debug)


def manage_users(gconn,
                 guac_params,
                 debug=False):
    """
    Manages the creation of user accounts and connections in Guacamole.

    Args:
        gconn: The connection to the Guacamole server.
        user_names: A dictionary containing the usernames and passwords of the users to be created.
        conn_instances: A list of connection instances.
        existing_accounts: A list of existing user accounts.
        conn_group_id: The ID of the connection group.
        guacamole_globals: A dictionary containing global Guacamole settings.
        heat_params: A dictionary containing Heat parameters.
        debug: A boolean indicating whether debug mode is enabled. Defaults to False.

    Returns:
        True if the provisioning of Guacamole is successful.
    """
    new_users = guac_params.get('new_users')
    instances = guac_params.get('instances')
    users = guac_params.get('users')
    conn_group_id = guac_params.get('conn_group_id')
    user_org = guac_params.get('user_org')
    conn_proto = guac_params.get('conn_proto')
    username = guac_params.get('username')
    password = guac_params.get('password')
    
    for guac_user in new_users:
        guac_password = new_users[guac_user]['password']

        if guac_user in users:
            error_msg("Guacamole ERROR:  Can't create user account, "
                      f"{guac_user} already exists.")
        else:
            general_msg(
                f"create_user_acct: {gconn}, {guac_user}, {guac_password}, {user_org}")

            # create_user_acct(
            #     gconn,
            #     guac_user,
            #     guac_password,
            #     user_org,
            #     debug)
            users.append(guac_user)

        # Create instance connections

        user_num = f"{guac_user}".rsplit('.', 1)[1]
        new_instances = [instance for instance in instances if instance['name'].endswith(
            f"{user_num}") and instance['name'].startswith(f"{guac_user}")]

        if new_instances == []:
            error_msg(f"Guacamole ERROR:  No instance was created, "
                      f"{guac_user} has no instances.")
        else:
            general_msg(
                f"create_user_conns: {gconn}, "
                f"{guac_user}, {new_instances}, "
                f"{conn_proto}, "
                f"{conn_group_id}, {username}, "
                f"{password}")

            # create_user_conns(
            #     gconn,
            #     guac_user,
            #     new_instances,
            #     conn_proto,
            #     conn_group_id,
            #     username,
            #     password,
            #     debug)


def get_existing_accounts(gconn, debug=False):
    """Locate existing user accounts"""
    existing_accounts = list(json.loads(gconn.list_users()))
    info_msg(existing_accounts, debug)
    return existing_accounts


def get_conn_groups(gconn, debug):
    """
    Get the connection group from the given gconn object.

    Parameters:
        gconn (object): The gconn object to retrieve the connection group from.
        debug (bool): If True, debug information will be printed.

    Returns:
        conn_groups (list): A list of connection groups.
    """
    conn_groups = json.loads(gconn.list_connection_groups())
    info_msg(conn_groups, debug)
    return conn_groups


def get_conn_group_id(gconn, conn_group_name, debug=False):
    """Locate connection group id"""
    conn_groups = json.loads(gconn.list_connection_groups())
    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == conn_group_name]
        info_msg(f"Retrieved {conn_group_name}'s group ID(s): {group_id}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_group_name}"
                  f" is missing from group list \n {error}")

    conn_group_id = group_id[0]
    if not conn_group_id:
        conn_group_id = None
    return conn_group_id


def get_conn_id(gconn, conn_name, conn_group_id, debug=False):
    """Locate connection id"""
    list_conns = json.loads(gconn.list_connections())
    try:
        conn_id = ([k for k, v in list_conns.items()
                   if v.get('parentIdentifier') == conn_group_id
                   and v.get('name') == conn_name])
        info_msg(f"Retrieved {conn_name}'s connection ID: {conn_id}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_name}"
                  f" is missing from connection list \n {error}")
    return conn_id


def create_conn_group(gconn, conn_group, parent_group="ROOT", debug=False):
    """Create connection group"""
    gconn.create_connection_group(
        conn_group,
        "ORGANIZATIONAL",
        parent_group,
        {
            'max-connections': '50',
            'max-connections-per-user': '10',
            'enable-session-affinity': ''
        }
    )
    time.sleep(2)
    info_msg(
        f"Guacamole:  The connection group {conn_group} was created", debug)


def delete_conn_group(gconn, conn_group_name, conn_group_id, debug=False):
    """Delete connection group"""
    gconn.delete_connection_group(conn_group_id)
    info_msg(f"Guacamole:  The connection group {conn_group_name} "
             f"with id: {conn_group_id} was deleted", debug)


def create_user_acct(gconn, user, guac_user_password, guac_user_organization, debug=False):
    """"Create user accounts"""
    gconn.create_user(user, guac_user_password,
                      {"guac-organization": guac_user_organization})
    info_msg(f"Guacamole:  Created User Account: {user}", debug)


def delete_user_acct(gconn, user, debug=False):
    """"Delete user accounts"""
    gconn.delete_user(user)
    info_msg(f'Guacamole:  Deleted User Account: {user}', debug)


def create_user_conns(gconn,
                      user,
                      instances,
                      conn_proto,
                      conn_group_id,
                      ostack_username,
                      ostack_pass,
                      debug=False):
    """Create user connections"""
    if instances == []:
        error_msg(f"Guacamole ERROR: User instance was not created, "
                  f"{user} was not created")
        return

    for instance in instances:
        if instance['address']:
            conn_name_ssh = f"{instance['name']}.ssh"
            conn_name_rdp = f"{instance['name']}.rdp"

            if "ssh" in conn_proto:
                conn_name = conn_name_ssh
            elif "rdp" in conn_proto:
                conn_name = conn_name_rdp
            else:
                continue

            if conn_name == conn_name_ssh:
                connection_type = "ssh"
            elif conn_name == conn_name_rdp:
                connection_type = "rdp"
            else:
                continue

            gconn.manage_connection(
                "post", connection_type, conn_name,
                conn_group_id, None,
                {
                    "hostname": instance['address'],
                    "port": "22" if connection_type == "ssh" else "3389",
                    "username": ostack_username,
                    "password": ostack_pass,
                    "security": "any" if connection_type == "rdp" else None,
                    "ignore-cert": "true" if connection_type == "rdp" else None
                },
                {
                    "max-connections": "",
                    "max-connections-per-user": "2"
                }
            )

            info_msg(f"Guacamole:  Created connection for {instance['name']}"
                     f" {connection_type} connection with address: {instance['address']}", debug)
            associate_user_conns(gconn, user, conn_name, conn_group_id)


def associate_user_conns(gconn, user, conn_name, conn_group_id, debug=False):
    """Associate user accounts with group_id and connections"""
    time.sleep(2)
    conn_id = get_conn_id(gconn, conn_name, conn_group_id)[0]
    gconn.update_user_connection(user, conn_group_id, "add", True)
    gconn.update_user_connection(user, conn_id, "add", False)
    info_msg(
        f"Guacamole:  Associated {conn_name} connection for {user}", debug)


def delete_user_conns(gconn, user, conn_name, conn_group_id, debug=False):
    """Delete user connections"""
    conn_id = get_conn_id(gconn, conn_name, conn_group_id)[0]
    gconn.delete_connection(conn_id)
    info_msg(f"Guacamole:  Deleted associated {conn_name}"
             f" connection for {user}", debug)
