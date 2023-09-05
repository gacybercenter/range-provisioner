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

    org_name = guac_params['org_name']
    conn_proto = guac_params['conn_proto']
    heat_user = guac_params['heat_user']
    heat_pass = guac_params['heat_pass']
    domain_name = guac_params['domain_name']
    instances = guac_params['instances']
    new_users = guac_params['new_users']
    new_groups = guac_params['new_groups']

    users_to_make = []
    guacd_ip = None

    for instance in instances:
        if instance['name'] in new_users.keys():
            instance['password'] = new_users.get(instance['name'])
            users_to_make.append(instance)
        elif "guacd" in instance['name']:
            guacd_ip = instance['public_v4']

    conn_groups = create_conn_groups(gconn,
                                     org_name,
                                     new_groups,
                                     debug)

    create_user_accts(gconn,
                      new_users,
                      org_name,
                      debug)

    create_user_conns(gconn,
                      users_to_make,
                      guacd_ip,
                      conn_proto,
                      heat_user,
                      heat_pass,
                      domain_name,
                      conn_groups,
                      debug)

    associate_user_conns(gconn,
                         users_to_make,
                         conn_groups,
                         debug)

    success_msg("Provisioned Guacamole")
    return True


def deprovision(gconn,
                guac_params,
                debug=False):
    """Deprovision Guacamole connections and users"""

    new_users = guac_params['new_users']
    new_groups = guac_params['new_groups']
    child_groups = guac_params['child_groups']

    users_to_delete = [new_user[0] for new_user in new_users.items()]

    groups_to_delete = []
    for group in new_groups:
        groups_to_delete.append(child_groups.get(group))

    delete_conn_groups(gconn,
                       groups_to_delete,
                       debug)

    delete_user_accts(gconn,
                      users_to_delete,
                      debug)

    success_msg("Deprovisioned Guacamole")
    return True

# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

# TODO(MCcrusader): Yeah, What he said. ^


def create_user_accts(gconn,
                      new_users,
                      user_org,
                      debug):
    """
    Creates user accounts based on each instance in the given list of instances.

    Args:
        gconn (object): The connection object for the Guacamole API.
        instances (list): A list of instances to create user accounts for.
        guac_user_password (str): The password for the user accounts.
        guac_user_organization (str): The organization for the user accounts.

    Returns:
        None
    """

    general_msg("Guacamole:  Creating User Accounts")
    users = new_users.items()
    for user in users:
        time.sleep(0.1)
        guac_user_name = user[0]
        guac_user_password = user[1]
        response = gconn.create_user(guac_user_name, guac_user_password,
                                     {"guac-organization": user_org})
        info_msg(f"Guacamole:  Created User: {guac_user_name}, "
                 f"Password: {guac_user_password} {response}", debug)


def get_existing_accounts(gconn, debug=False):
    """Locate existing user accounts"""

    existing_accounts = list(json.loads(gconn.list_users()))
    return existing_accounts


def get_conn_group_id(gconn, org_name, debug=False):
    """Locate connection group id"""

    conn_groups = json.loads(gconn.list_connection_groups())
    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == org_name]
        return_id = group_id[0]
        info_msg(f"Guacamole:  Retrieved {org_name}'s "
                 f"group ID(s): {group_id}", debug)

    except IndexError:
        error_msg(f"Guacamole ERROR:  {org_name} "
                  "has no connection group ID(s)")
        return_id = None
    return return_id


def get_child_groups(gconn, conn_group_id, debug=False):
    """Locate connection id"""

    list_conns = json.loads(gconn.list_connection_groups())
    conn_groups = {}
    try:
        for conn in list_conns.values():
            if conn.get('parentIdentifier') == conn_group_id:
                conn_groups[conn.get('name')] = conn.get('identifier')
        info_msg(f"Guacamole:  Retrieved {conn_group_id}'s "
                 f"child groups: {conn_groups}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_group_id} "
                  f"has no child groups  {error}")
    return conn_groups


def get_conn_id(gconn,
                conn_name,
                conn_group_id,
                debug=False):
    """Locate connection id"""

    list_conns = json.loads(gconn.list_connections())
    try:
        conn_id = [conn['identifier'] for conn in list_conns.values()
                   if conn['parentIdentifier'] == conn_group_id
                   and conn['name'] == conn_name][0]
        info_msg(
            f"Guacamole:  Retrieved {conn_name}'s connection ID: {conn_id}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_name} "
                  f"is missing from connection list  {error}")
    return conn_id


def create_conn_groups(gconn,
                       conn_group,
                       new_groups,
                       debug=False):
    """Create connection group"""

    general_msg("Guacamole:  Creating connection groups")
    conn_groups = {}
    conn_groups[conn_group] = create_group(gconn,
                                           'ROOT',
                                           conn_group,
                                           debug)

    parent_id = conn_groups[conn_group]

    for group in new_groups:
        conn_groups[group] = create_group(gconn,
                                            parent_id,
                                            group,
                                            debug)

    return conn_groups

def create_group(gconn,
                 parent,
                 child,
                 debug=False):
    """Create connection group"""
    response = gconn.create_connection_group(
        child,
        "ORGANIZATIONAL",
        parent,
        {
            'max-connections': '50',
            'max-connections-per-user': '10',
            'enable-session-affinity': None
        }
    )
    info_msg(f"Guacamole:  Made group {child} under {parent}, "
            f"{response}", debug)
    time.sleep(0.1)

    group_id = get_conn_group_id(gconn, child, debug)
    time.sleep(0.1)

    return group_id


def delete_conn_groups(gconn,
                       group_ids,
                       debug=False):
    """Delete connection group"""

    general_msg("Guacamole:  Deleting connection groups")
    for group_id in group_ids:
        response = gconn.delete_connection_group(group_id)
        info_msg(f"Guacamole:  Deleted Group ID: {group_id} "
                 f"{response}", debug)
        time.sleep(0.1)


def create_user_conns(gconn,
                      users,
                      guacd_ip,
                      protocol,
                      conn_user,
                      conn_pass,
                      domain_name,
                      conn_groups,
                      debug=False):
    """
    Create user connections.

    Parameters:
    - gconn: The GConn object used for managing connections.
    - instances: A list of instances.
    - guacd_ip: The IP address of the Guacamole server.
    - conn_group_id: The ID of the connection group.

    Returns:
    - None

    Description:
    This function creates user connections for each instance in the provided list.
    It replaces a specific string in the connection name and retrieves the private 
    IPv4 IP address from each instance. It then uses the gconn object to manage
    the connection by making a POST request to the Guacamole server.
    If any exception occurs during the process, an error message is printed.
    Finally, the function prints the details of the created connection.

    Note:
    - The instances list should not be empty.
    - The connection name is modified by replacing a specific string.
    - The default username and password for the connection are hardcoded in the function.
    - The maximum number of connections and maximum connections per user are set to 2.
    - The security parameter is set to "any".
    - The ignore-cert parameter is set to "true".
    - The guacd-hostname parameter is set to the provided guacd_ip.
    """

    if users == []:
        error_msg("Guacamole ERROR:  There are no instances to be mapped")
        return

    if guacd_ip is not None:
        general_msg("Guacamole:  Found Guacd server, "
                    f"IP: {guacd_ip}")
    else:
        general_msg("Guacamole:  No Guacd server found")

    general_msg("Guacamole:  Creating user connections")

    for user in users:
        time.sleep(0.1)
        conn_name = user['name']
        conn_org = conn_name.split('.')[0]
        conn_group_id = conn_groups[conn_org]
        conn_ip = user['public_v4'] if guacd_ip is None else user['private_v4']
        try:
            gconn.manage_connection(
                "post", protocol, conn_name,
                conn_group_id, None,
                {
                    "hostname": conn_ip,
                    "port": "3389" if protocol == "rdp" else "22",
                    "username": conn_user,
                    "password": conn_pass,
                    "domain": domain_name,
                    "security": "any" if protocol == "rdp" else None,
                    "ignore-cert": "true" if protocol == "rdp" else None
                },
                {
                    "max-connections": "1",
                    "max-connections-per-user": "1",
                    "guacd-hostname": guacd_ip
                }
            )
        except Exception as error:
            error_msg(f"Failed to create {conn_name} Guacamole connection "
                      f"{error}")
        info_msg(f"Guacamole:  Created Guacamole Connection: {conn_name}.\n "
                 f"User: {conn_user}, Password: {conn_pass}, IP: {conn_ip}", debug)


def associate_user_conns(gconn,
                         users,
                         conn_groups,
                         debug=False):
    """Associate user accounts with group_id and connections"""

    general_msg("Guacamole:  Associating user connections")
    for user in users:
        conn_name = user['name']
        conn_org = conn_name.split('.')[0]
        conn_group_id = conn_groups[conn_org]
        time.sleep(0.5)

        conn_id = get_conn_id(gconn, conn_name, conn_group_id, debug)
        response = gconn.update_user_connection(
            conn_name, conn_group_id, "add", True)
        info_msg(f"Guacamole:  Associated {conn_name} to group: {conn_group_id} "
                 f"{response},", debug)

        response = gconn.update_user_connection(
            conn_name, conn_id, "add", False)
        info_msg(f"Guacamole:  Associated {conn_name} to connection: {conn_id} "
                 f"{response},", debug)


def delete_user_conns(gconn,
                      conn_name,
                      conn_group_id,
                      debug=False):
    """Delete user connections"""

    general_msg("Guacamole:  Deleting user connections")
    conn_id = get_conn_id(gconn, conn_name, conn_group_id)[0]
    response = gconn.delete_connection(conn_id)
    info_msg(f"Guacamole:  Deleted Connection: {conn_name} "
             f"{response},", debug)


def delete_user_accts(gconn,
                      users,
                      debug=False):
    """"Delete user accounts"""

    general_msg("Guacamole:  Deleting user accounts")
    for user in users:
        response = gconn.delete_user(user)
        info_msg(f"Guacamole:  Deleted Account: {user} "
                 f"{response}", debug)


def get_domain_name(heat_params,
                    debug=False):
    """
    Retrieves the domain name from the given heat parameters.

    Parameters:
        heat_params (dict): The heat parameters from which to retrieve the domain name.
        debug (bool, optional): A flag indicating whether debugging information should
        be displayed. Defaults to False.

    Returns:
        str: The retrieved domain name.

    Raises:
        KeyError: If the domain name is not found in the heat parameters.
    """
    try:
        domain_name = heat_params['domain_name']['default']
        info_msg(f"Guacamole:  Retrieved domain name: {domain_name}", debug)
        return domain_name
    except KeyError:
        info_msg("Guacamole:  Did not find a domain name", debug)
        return None
