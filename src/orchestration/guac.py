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

    create_vars, guacd_ips = create_data(guac_params)

    conn_groups = create_conn_groups(gconn,
                                     create_vars['groups'],
                                     guac_params['parent_group_id'],
                                     guac_params['org_name'],
                                     debug)

    create_user_accts(gconn,
                      create_vars['users'],
                      guac_params['org_name'],
                      debug)

    conns = create_user_conns(gconn,
                              create_vars['conns'],
                              conn_groups,
                              guacd_ips,
                              debug)

    associate_user_conns(gconn,
                         create_vars['mappings'],
                         guac_params['org_name'],
                         conn_groups,
                         conns,
                         debug)

    success_msg("Provisioned Guacamole")
    return True


def deprovision(gconn,
                guac_params,
                debug=False):
    """Deprovision Guacamole connections and users"""

    delete_vars = delete_data(guac_params)

    delete_conn_groups(gconn,
                       delete_vars['groups'],
                       debug)

    delete_user_accts(gconn,
                      delete_vars['users'],
                      debug)

    delete_user_conns(gconn,
                      delete_vars['conns'],
                      debug)

    success_msg("Deprovisioned Guacamole")
    return True


def reprovision(gconn,
                guac_params,
                debug=False):
    """Reprovision Guacamole connections and users"""

    create_vars, delete_vars, guacd_ips = update_data(guac_params)

    delete_conn_groups(gconn,
                       delete_vars['groups'],
                       debug)

    delete_user_accts(gconn,
                      delete_vars['users'],
                      debug)

    delete_user_conns(gconn,
                      delete_vars['conns'],
                      debug)

    conn_groups = create_conn_groups(gconn,
                                     create_vars['groups'],
                                     guac_params['parent_group_id'],
                                     guac_params['org_name'],
                                     debug)

    create_user_accts(gconn,
                      create_vars['users'],
                      guac_params['org_name'],
                      debug)

    conns = create_user_conns(gconn,
                              create_vars['conns'],
                              conn_groups,
                              guacd_ips,
                              debug)

    associate_user_conns(gconn,
                         create_vars['mappings'],
                         guac_params['org_name'],
                         conn_groups,
                         conns,
                         debug)

    success_msg("Reprovisioned Guacamole")
    return True


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

# TODO(MCcrusade): Yeah, What he said. ^


def create_data(guac_params: dict) -> tuple:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        tuple: A tuple containing the create data and the Guacd IPs.
    """

    # Extract parameters from guac_params
    new_users = guac_params['new_users']
    new_groups = guac_params['new_groups']
    instances = guac_params['instances']
    guacd_ips = {}

    # Process each instance
    for instance in instances:
        # Set protocol and params for the instance
        instance['protocol'] = guac_params['protocol']
        instance['params'] = {
            'hostname': instance['hostname'],
            'username': guac_params['username'],
            'password': guac_params['password'],
            "domain": guac_params['domain_name'],
            "port": "3389" if instance['protocol'] == "rdp" else "22",
            "security": "any" if instance['protocol'] == "rdp" else "",
            "ignore-cert": "true" if instance['protocol'] == "rdp" else ""
        }
        # Remove hostname from instance
        del instance['hostname']

        # Remove empty values from params
        for key, value in instance['params'].copy().items():
            if not value:
                del instance['params'][key]

        # Extract guacd IPs
        if "guacd" in instance['name']:
            guacd_org = instance['name'].split('.')[0]
            guacd_ips[guacd_org] = instance['params']['hostname']

    # Initialize variables
    create_groups = new_groups
    create_users = []
    create_conns = []
    mappings = []

    # Generate the create data based on the new user mapping data
    for username, data in new_users.items():
        # Create user dictionary
        create_users.append(
            {
                username: data['password']
            }
        )
        # Create mapping dictionary
        mappings.append(
            {
                username: [instance['name'] for instance in instances
                           if instance['name'] in data['instances']]
            }
        )
        # Get instances for user connections
        conn_instances = [instance for instance in instances
                          if instance['name'] in data['instances']]
        # Add creates the connection if not already created
        for instance in conn_instances:
            if instance not in create_conns:
                create_conns.append(instance)

    # Return the created data and guacd IPs
    return ({
        'groups': create_groups,
        'users': create_users,
        'conns': create_conns,
        'mappings': mappings
    }, guacd_ips)


def delete_data(guac_params: object) -> dict:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        dict: A dictionary containing the delete data.

    """

    # Get the group IDs, users, and connections to be deleted
    delete_group_ids = guac_params['conn_group_ids']
    delete_users = guac_params['conn_users']
    delete_conns = guac_params['conn_list']

    # Remove connections that belong to the specified group IDs
    delete_conns = [conn for conn in delete_conns
                    if conn['parentIdentifier'] not in delete_group_ids]

    # Get the connection IDs of the remaining connections
    delete_conn_ids = [conn['identifier'] for conn in delete_conns]

    # Return the deleted group IDs, users, and connection IDs
    return {
        'groups': delete_group_ids,
        'users': delete_users,
        'conns': delete_conn_ids,
    }


def update_data(guac_params: dict) -> tuple:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        tuple: A tuple containing the create data, delete data, and the Guacd IPs.
    """

    # Extract necessary data from guac_params
    create_vars, guacd_ips = create_data(guac_params)

    # Extract necessary data from guac_params
    conn_groups = guac_params['conn_groups']
    conn_users = guac_params['conn_users']
    conn_list = guac_params['conn_list']

    # Get the names of current groups, users, and connections
    current_groups = [group['name'] for group in conn_groups]
    current_users = conn_users
    current_conns = conn_list.copy()
    current_conn_ids = {
                            conn['name']: conn['identifier']
                            for conn in current_conns
                        }

    # Initialize lists to store IDs of items to delete
    delete_group_ids = []
    delete_conn_ids = []
    delete_users = []

    # Get the names of users and connections to create
    create_usernames = [list(user.keys())[0] for user in create_vars['users']]

    # Check if any groups need to be deleted
    for group in current_groups:
        if group not in create_vars['groups']:
            delete_group_ids.append(group['identifier'])

    # Remove connections that belong to groups to be deleted
    current_conns = [conn for conn in current_conns
                     if conn['parentIdentifier'] not in delete_group_ids]

    # Check if any users need to be deleted
    for user in current_users:
        if user not in create_usernames:
            delete_users.append(user)

    # Remove keys and only delete conns with existing parent groups
    for conn in current_conns:
        del conn['identifier']
        del conn['parentIdentifier']
        if conn not in create_vars['conns']:
            delete_conn_ids.append(current_conn_ids[conn['name']])

    # Return the formatted data
    return (
        {
            'groups': create_vars['groups'],
            'users': create_vars['users'],
            'conns': create_vars['conns'],
            'mappings': create_vars['mappings']
        },
        {
            'groups': delete_group_ids,
            'users': delete_users,
            'conns': delete_conn_ids
        }, guacd_ips)


def create_conn_groups(gconn: object,
                       create_groups: list,
                       conn_group_id: str,
                       org_name: str,
                       debug=False) -> dict:
    """Create connection group"""

    general_msg("Guacamole:  Creating Connection Groups")
    conn_groups = create_parent_group(gconn,
                                      conn_group_id,
                                      org_name,
                                      debug)
    parent_id = conn_groups[org_name]

    if create_groups:
        for group in create_groups:
            conn_groups[group] = create_group(gconn,
                                              parent_id,
                                              group,
                                              False,
                                              debug)
        time.sleep(0.1)
    else:
        general_msg("Guacamole:  No Connection Groups to Create")

    return conn_groups


def delete_conn_groups(gconn: object,
                       group_ids: list,
                       debug=False) -> None:
    """Delete connection group"""

    if not group_ids:
        general_msg("Guacamole:  No Connection Groups to Delete")
        return

    general_msg("Guacamole:  Deleting Connection Groups")
    for group_id in group_ids:
        delete_group(gconn,
                     group_id,
                     debug)
        time.sleep(0.1)


def create_parent_group(gconn: object,
                        conn_group_id: str | None,
                        org_name: str,
                        debug=False) -> dict:
    """Creates the parent connection group"""

    conn_groups = {}
    if conn_group_id:
        general_msg(f"Guacamole:  {org_name} Already Exists")
        conn_groups[org_name] = conn_group_id
    else:
        general_msg(f"Guacamole:  Creating Orginization: {org_name}")
        conn_groups[org_name] = create_group(gconn,
                                             'ROOT',
                                             org_name,
                                             False,
                                             debug)
        time.sleep(0.1)

    return conn_groups


def create_group(gconn: object,
                 parent_id: str,
                 child_name: str,
                 child_id: str | None,
                 debug=False) -> str:
    """Create connection group"""

    if child_id:
        response = gconn.update_connection_group(
            child_id,
            child_name,
            "ORGANIZATIONAL",
            parent_id,
            {
                'max-connections': '50',
                'max-connections-per-user': '10',
                'enable-session-affinity': ''
            }
        )
        time.sleep(0.1)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Updated Group: "
                     f"{child_name} under group ID: {parent_id}", debug)
    else:
        response = gconn.create_connection_group(
            child_name,
            "ORGANIZATIONAL",
            parent_id,
            {
                'max-connections': '50',
                'max-connections-per-user': '10',
                'enable-session-affinity': ''
            }
        )
        time.sleep(0.1)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Created Group: "
                     f"{child_name} under group ID: {parent_id}", debug)
        child_id = get_conn_group_id(gconn,
                                     child_name,
                                     debug)
        time.sleep(0.1)

    return child_id


def delete_group(gconn: object,
                 group_id: str,
                 debug=False) -> None:
    """Delete connection group"""
    response = gconn.delete_connection_group(group_id)
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    else:
        info_msg("Guacamole:  Deleted Group ID: "
                 f"{group_id}", debug)


def create_user_accts(gconn: object,
                      create_users: list,
                      user_org: str,
                      debug=False) -> None:
    """Creates user accounts based on a lists of instances"""

    if not create_users:
        general_msg("Guacamole:  No Users Accounts to Create")
        return

    general_msg("Guacamole:  Creating User Accounts")
    for user in create_users:
        create_user(gconn,
                    user,
                    user_org,
                    debug)


def delete_user_accts(gconn: object,
                      delete_users: list,
                      debug=False) -> None:
    """"Delete user accounts"""

    if not delete_users:
        general_msg("Guacamole:  No Users Accounts to Delete")
        return

    general_msg("Guacamole:  Deleting User Accounts")
    for user in delete_users:
        delete_user(gconn,
                    user,
                    debug)


def create_user(gconn: object,
                user: dict,
                user_org: str,
                debug=False) -> None:
    """Creates a user account based on a dictionary"""
    username = list(user.keys())[0]
    password = list(user.values())[0]

    response = gconn.create_user(username, password,
                                 {"guac-organization": user_org})
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    else:
        info_msg(f"Guacamole:  Created User: {username}, "
                 f"Password: {password}", debug)
    time.sleep(0.1)


def delete_user(gconn: object,
                user: str,
                debug=False) -> None:
    """Deletes a user account based on a string"""
    response = gconn.delete_user(user)
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    else:
        info_msg("Guacamole:  Deleted Account: "
                 f"{user}", debug)
    time.sleep(0.1)


def create_user_conns(gconn: object,
                      create_conns: list,
                      conn_groups: dict,
                      guacd_ips: dict,
                      debug=False):
    """Create user connections"""

    if not create_conns:
        general_msg("Guacamole:  No User Connections to Create")
        return

    general_msg("Guacamole:  Creating User Connections")
    conns = {}
    if guacd_ips:
        general_msg("Guacamole:  Found Guacd servers. ")
        info_msg(f"Guacamole:  {json.dumps(guacd_ips, indent=4)}", debug)
    else:
        general_msg("Guacamole:  No Guacd servers found")

    for conn in create_conns:
        conn_name = conn['name']
        conns[conn_name] = create_conn(gconn,
                                       conn,
                                       conn_groups,
                                       guacd_ips,
                                       None,
                                       debug)

    return conns


def delete_user_conns(gconn: object,
                      delete_conn_ids: list,
                      debug=False) -> None:
    """Delete user connections"""

    if not delete_conn_ids:
        general_msg("Guacamole:  No User Connections to Delete")
        return

    general_msg("Guacamole:  Deleting User Connections")
    for conn_id in delete_conn_ids:
        delete_conn(gconn,
                    conn_id,
                    debug)


def create_conn(gconn: object,
                conn: dict,
                conn_groups: dict,
                guacd_ips: dict,
                conn_id: str | None,
                debug=False) -> None:
    """Create a user connection."""

    conn_proto = conn['protocol']
    conn_name = conn['name']
    conn_org = conn_name.split('.')[0]
    conn_group_id = conn_groups[conn_org]

    if conn_id:
        req_type = "put"
        update = True
    else:
        req_type = "post"
        update = False

    response = gconn.manage_connection(
        req_type, conn_proto, conn_name,
        conn_group_id, conn_id,
        conn['params'],
        {
            "max-connections": "1",
            "max-connections-per-user": "1",
            "guacd-hostname": guacd_ips.get(conn_org, "")
        }
    )
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
        time.sleep(0.1)
        conn_id = get_conn_id(gconn,
                              conn_name,
                              conn_group_id,
                              debug)
    elif update:
        info_msg(f"Guacamole:  Updated User Connection: {conn_name}. "
                 f"({conn['params']['username']}, {conn['params']['password']}) "
                 f"IP: {conn['params']['hostname']}", debug)
    else:
        info_msg(f"Guacamole:  Created User Connection: {conn_name}. "
                 f"({conn['params']['username']}, {conn['params']['password']}) "
                 f"IP: {conn['params']['hostname']}", debug)
        time.sleep(0.1)
        conn_id = get_conn_id(gconn,
                              conn_name,
                              conn_group_id,
                              debug)
    time.sleep(0.1)

    return conn_id


def delete_conn(gconn: object,
                conn_id: str,
                debug=False) -> None:
    """Delete a user connection."""

    response = gconn.delete_connection(conn_id)
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    else:
        info_msg("Guacamole:  Deleted Connection ID: "
                 f"{conn_id}", debug)
    time.sleep(0.1)


def associate_user_conns(gconn: object,
                         mappings: dict,
                         org_name: str,
                         conn_groups: dict,
                         conn_ids: dict,
                         debug=False) -> None:
    """Associate user accounts with group_id and connections"""

    if not mappings:
        general_msg("Guacamole:  No User Connections to Associate")
        return

    general_msg("Guacamole:  Associating User Connections")

    for mapping in mappings:
        user_name = list(mapping.keys())[0]
        conn_names = list(mapping.values())[0]
        parent_id = conn_groups[org_name]
        groups = []

        associate_conn(gconn,
                       user_name,
                       parent_id,
                       True,
                       org_name,
                       debug)

        for conn_name in conn_names:
            group = conn_name.split('.')[0]
            conn_group_id = conn_groups[group]
            if group not in groups:
                groups.append(group)
                associate_conn(gconn,
                               user_name,
                               conn_group_id,
                               True,
                               group,
                               debug)

            conn_id = conn_ids[conn_name]
            associate_conn(gconn,
                           user_name,
                           conn_id,
                           False,
                           conn_name,
                           debug)


def associate_conn(gconn: object,
                   user_name: str,
                   conn_id: str,
                   is_group: bool,
                   conn_name=False,
                   debug=False) -> None:
    """Associate user accounts with group_ids and connections"""
    response = gconn.update_user_connection(
        user_name, conn_id, "add", is_group)
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}")
    elif conn_name:
        info_msg(f"Guacamole:  Associated {user_name} "
                 f"to connection: {conn_name} ({conn_id})", debug)
    else:
        info_msg(f"Guacamole:  Associated {user_name} "
                 f"to connection id: {conn_id}", debug)
    time.sleep(0.1)


def get_conn_group_id(gconn: object,
                      org_name: str,
                      debug=False) -> str:
    """Locate connection group id"""

    conn_groups = json.loads(gconn.list_connection_groups())
    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == org_name]
        return_id = group_id[0]
        info_msg(f"Guacamole:  Retrieved {org_name}'s "
                 f"group ID: {return_id}", debug)

    except IndexError:
        error_msg(f"Guacamole ERROR:  {org_name} "
                  "has no connection group ID(s)")
        return_id = None
    return return_id


def get_conn_id(gconn: object,
                conn_name: str,
                conn_group_id: str,
                debug=False) -> str:
    """Locate connection id"""
    conn_list = json.loads(gconn.list_connections())
    try:
        conn_id = [conn['identifier'] for conn in conn_list.values()
                   if conn['parentIdentifier'] == conn_group_id
                   and conn['name'] == conn_name][0]
        info_msg(
            f"Guacamole:  Retrieved {conn_name}'s connection ID: {conn_id}", debug)

    except IndexError as error:
        conn_id = []
        error_msg(f"Guacamole ERROR:  {conn_name} "
                  f"is missing from connection list  {error}")
    return conn_id


def get_groups(gconn: object,
               parent_id: str,
               debug=False) -> dict:
    """Get connection group data from Guacamole"""

    all_conn_groups = json.loads(gconn.list_connection_groups())
    conn_groups = [group for group in all_conn_groups.values()
                   if group['parentIdentifier'] == parent_id]
    info_msg("Guacamole:  Retrieved connection groups:", debug)
    info_msg(conn_groups, debug)
    return conn_groups


def get_conns(gconn: object,
              conn_group_ids: dict,
              debug=False) -> dict:
    """Get connection data from Guacamole"""

    conns = [
        {
            'name': conn['name'],
            'identifier': conn['identifier'],
            'parentIdentifier': conn['parentIdentifier'],
            'protocol': conn['protocol']
        }
        for conn in json.loads(gconn.list_connections()).values()
        if conn['parentIdentifier'] in conn_group_ids
    ]
    for conn in conns:
        conn['params'] = json.loads(
            gconn.detail_connection(conn['identifier'], "params")
        )
    info_msg("Guacamole:  Retrieved connections:", debug)
    info_msg(conns, debug)
    return conns


def get_users(gconn: object,
              org_name: str,
              debug=False) -> dict:
    """Get user data from Guacamole"""

    all_users = json.loads(gconn.list_users())
    users = [user['username'] for user in all_users.values()
             if user['attributes']['guac-organization'] == org_name]
    info_msg("Guacamole:  Retrieved users:", debug)
    info_msg(users, debug)
    return users


def find_domain_name(heat_params: dict,
                     debug=False) -> str:
    """Locates the domain name from the given heat parameters."""

    try:
        domain_name = heat_params['domain_name']['default']
        info_msg(f"Guacamole:  Retrieved domain name: {domain_name}", debug)
        return domain_name
    except KeyError:
        info_msg("Guacamole:  Did not find a domain name", debug)
        return ''


def find_group_ids(conn_list: list,
                   debug=False) -> dict:
    """Locates the child groups and their connection ids"""

    conn_group_ids = [
        conn['identifier'] for conn in conn_list
    ]
    info_msg("Guacamole:  Found connection group IDs:", debug)
    info_msg(conn_group_ids, debug)
    return conn_group_ids


def find_conn_id(conn_list: list,
                 conn_name: str,
                 conn_group_id: str,
                 debug=False) -> str:
    """Locates a user connection id"""

    try:
        conn_id = [conn['identifier'] for conn in conn_list.values()
                   if conn['parentIdentifier'] == conn_group_id
                   and conn['name'] == conn_name][0]
        info_msg(
            f"Guacamole:  Found {conn_name}'s connection ID: {conn_id}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_name} "
                  f"is missing from connection list  {error}")
    return conn_id


def parse_response(response: object) -> str:
    """Parse the response from the Guacamole API"""

    try:
        message = response.json().get('message')
    except json.decoder.JSONDecodeError:
        return ''
    if not message:
        return ''
    return message
