"""
Author: Marcus Corulli
Description: Provision and Deprovision Guacamole
Date: 09/28/2023
Version: 1.0

Description:
    Contains all the main functions for provisioning Guacamole
"""
import json
import time
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(gconn: object,
              guac_params: dict,
              debug: bool = False) -> bool:
    """
    Provisions Guacamole with the given parameters.

    Args:
        gconn (object): Connection to the Guacamole server.
        guac_params (dict): Parameters for provisioning Guacamole.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    general_msg("Provisioning Guacamole",
                endpoint)

    try:
        # Generate the create data
        create_vars, guacd_ips = create_data(guac_params)

        # Create connection groups
        conn_groups = create_conn_groups(gconn,
                                         create_vars['groups'],
                                         guac_params['parent_group_id'],
                                         guac_params['org_name'],
                                         debug)

        # Create user accounts
        create_user_accts(gconn,
                          create_vars['users'],
                          guac_params['org_name'],
                          debug)

        # Create user connections
        conns = create_user_conns(gconn,
                                  create_vars['conns'],
                                  conn_groups,
                                  guacd_ips,
                                  debug)

        # Associate user connections
        associate_user_conns(gconn,
                             create_vars['mappings'],
                             guac_params['org_name'],
                             conn_groups,
                             conns,
                             debug)

    except Exception as error:
        error_msg(error,
                  endpoint)
        return

    success_msg("Provisioned Guacamole",
                endpoint)


def deprovision(gconn: object,
                guac_params: dict,
                debug: bool = False) -> bool:
    """
    Deprovision Guacamole connections and users.

    Args:
        gconn (object): The Guacamole connection object.
        guac_params (dict): The parameters for Guacamole.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    general_msg("Deprovisioning Guacamole",
                endpoint)

    try:
        # Generate the delete data
        delete_vars = delete_data(guac_params)

        # Delete connection groups
        delete_conn_groups(gconn,
                           delete_vars['groups'],
                           debug)

        # Delete user accounts
        delete_user_accts(gconn,
                          delete_vars['users'],
                          debug)

        # Delete user connections
        delete_user_conns(gconn,
                          delete_vars['conns'],
                          debug)

    except Exception as error:
        error_msg(error,
                  endpoint)
        return

    success_msg("Deprovisioned Guacamole",
                endpoint)


def reprovision(gconn: object,
                guac_params: dict,
                debug: bool = False) -> bool:
    """
    Reprovisions Guacamole connections and users.

    Args:
        gconn (object): The Guacamole connection object.
        guac_params (dict): The parameters for Guacamole connections and users.
        debug (bool, optional): Whether to run in debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    general_msg("Updating Guacamole",
                endpoint)

    try:
        # Generate the update data
        create_vars, delete_vars, guacd_ips = update_data(guac_params)

        # Delete connection groups
        delete_conn_groups(gconn,
                           delete_vars['groups'],
                           debug)

        # Delete user accounts
        delete_user_accts(gconn,
                          delete_vars['users'],
                          debug)

        # Delete user connections
        delete_user_conns(gconn,
                          delete_vars['conns'],
                          debug)

        # Create connection groups
        conn_groups = create_conn_groups(gconn,
                                         create_vars['groups'],
                                         guac_params['parent_group_id'],
                                         guac_params['org_name'],
                                         debug)

        # Create user accounts
        create_user_accts(gconn,
                          create_vars['users'],
                          guac_params['org_name'],
                          debug)

        # Create user connections
        conns = create_user_conns(gconn,
                                  create_vars['conns'],
                                  conn_groups,
                                  guacd_ips,
                                  debug)

        # Associate user connections with user accounts and connection groups
        associate_user_conns(gconn,
                             create_vars['mappings'],
                             guac_params['org_name'],
                             conn_groups,
                             conns,
                             debug)

    except Exception as error:
        error_msg(error,
                  endpoint)
        return

    success_msg("Updated Guacamole",
                endpoint)


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
    return (
        {
            'groups': create_groups,
            'users': create_users,
            'conns': create_conns,
            'mappings': mappings
        },
        guacd_ips
    )


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

    # Get the name: id pairs of current groups and connections
    current_group_ids = {
        group['name']: group['identifier']
        for group in conn_groups
    }
    current_conn_ids = {
        conn['name']: conn['identifier']
        for conn in conn_list
    }

    # Initialize lists to store IDs of items to delete
    delete_group_ids = []
    delete_conn_ids = []
    delete_users = []

    # Get the names of users and connections to create
    create_usernames = [list(user.keys())[0] for user in create_vars['users']]

    # Check if any groups need to be deleted
    for group in conn_groups:
        if group['name'] not in create_vars['groups']:
            delete_group_ids.append(current_group_ids[group['name']])

    # Remove connections that belong to groups to be deleted
    current_conns = [conn for conn in conn_list
                     if conn['parentIdentifier'] not in delete_group_ids]

    # Check if any users need to be deleted
    for user in conn_users:
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
        create_vars,
        {
            'groups': delete_group_ids,
            'users': delete_users,
            'conns': delete_conn_ids
        },
        guacd_ips
    )


def create_conn_groups(gconn: object,
                       create_groups: list,
                       conn_group_id: str,
                       org_name: str,
                       debug: bool = False) -> dict:
    """
    Create connection groups in Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        create_groups (list): A list of connection groups to create.
        conn_group_id (str): The ID of the parent connection group.
        org_name (str): The name of the organization.
        debug (bool, optional): Whether to print debug messages. Defaults to False.

    Returns:
        dict: A dictionary containing the created connection groups.
    """

    endpoint = 'Guacamole'

    general_msg("Creating Connection Groups",
                endpoint)

    # Create the parent connection group
    conn_groups = create_parent_group(gconn,
                                      conn_group_id,
                                      org_name,
                                      debug)
    parent_id = conn_groups[org_name]

    if not create_groups:
        general_msg("No Connection Groups to Create",
                    endpoint)
        return conn_groups

    # Create each connection group in the list
    for group in create_groups:
        conn_groups[group] = create_group(gconn,
                                          parent_id,
                                          group,
                                          False,
                                          debug)
    time.sleep(0.1)

    return conn_groups


def delete_conn_groups(gconn: object,
                       group_ids: list,
                       debug: bool = False) -> None:
    """
    Delete connection groups in Guacamole.

    Args:
        gconn (object): The connection object.
        group_ids (list): List of group IDs to delete.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.
    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Check if there are no group IDs to delete
    if not group_ids:
        general_msg("No Connection Groups to Delete",
                    endpoint)
        return

    general_msg("Deleting Connection Groups",
                endpoint)

    # Iterate over the group IDs and delete each group
    for group_id in group_ids:
        delete_group(gconn,
                     group_id,
                     debug)
        time.sleep(0.1)


def create_parent_group(gconn: object,
                        conn_group_id: str | None,
                        org_name: str,
                        debug: bool = False) -> dict:
    """
    Creates the parent connection group in Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        conn_group_id (str | None): The ID of the connection group, if it already exists.
        org_name (str): The name of the organization.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        dict: A dictionary containing the parent connection group.
    """

    endpoint = 'Guacamole'
    conn_groups = {}

    # Check if the parent connection group already exists
    if conn_group_id:
        general_msg(F"The parent group '{org_name}' already exists.",
                    endpoint)
        conn_groups[org_name] = conn_group_id
    else:
        # Create the parent connection group
        general_msg(f"Creating Organization '{org_name}'",
                    endpoint)
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
                 debug: bool = False) -> str:
    """
    Create or update a group in Guacamole.

    Args:
        gconn (object): The connection object.
        parent_id (str): The ID of the parent group.
        child_name (str): The name of the child group.
        child_id (str | None): The ID of the child group, if it already exists.
        debug (bool): Enable debug mode.

    Returns:
        str: The ID of the child group.

    """

    endpoint = 'Guacamole'

    # Check if child_id is provided
    if child_id:
        # Update the connection group
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
            info_msg(f"{message}",
                     endpoint,
                     debug)
        else:
            info_msg(f"Updated Group '{child_name}' under group ID '{parent_id}'",
                     endpoint,
                     debug)
    else:
        # Create the connection group
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
        # Manage the response
        message = parse_response(response)
        if message:
            info_msg(f"{message}",
                     endpoint,
                     debug)
        else:
            info_msg(f"Created Group '{child_name}' under group ID '{parent_id}'",
                     endpoint,
                     debug)
        # Get the connection group ID
        child_id = get_conn_group_id(gconn,
                                     child_name,
                                     debug)
        time.sleep(0.1)

    return child_id


def delete_group(gconn: object,
                 group_id: str,
                 debug: bool = False) -> None:
    """
    Deletes a connection group from Guacamole.

    Args:
        gconn (object): The connection object for interacting with Guacamole.
        group_id (str): The ID of the group to be deleted.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Delete the connection group
    response = gconn.delete_connection_group(group_id)

    # Parse the response message
    message = parse_response(response)

    # Check if there is a message and print it
    if message:
        info_msg(f"{message}",
                 endpoint,
                 debug)
    else:
        # If no message, print the deleted group ID
        info_msg(f"Deleted Group ID '{group_id}'",
                 endpoint,
                 debug)


def create_user_accts(gconn: object,
                      create_users: list,
                      user_org: str,
                      debug: bool = False) -> None:
    """
    Create user accounts in Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        create_users (list): List of user accounts to create.
        user_org (str): The user organization.
        debug (bool, optional): Enable debug mode. Defaults to False.
    """

    endpoint = 'Guacamole'

    # Check if there are no users to create
    if not create_users:
        general_msg("No Users Accounts to Create",
                    endpoint)
        return

    general_msg("Creating User Accounts",
                endpoint)
    # Create user accounts
    for user in create_users:
        create_user(gconn,
                    user,
                    user_org,
                    debug)


def delete_user_accts(gconn: object,
                      delete_users: list,
                      debug: bool = False) -> None:
    """
    Delete user accounts

    Args:
        gconn (object): The Guacamole connection object.
        delete_users (list): A list of user accounts to delete.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Check if there are any user accounts to delete
    if not delete_users:
        general_msg("No User Accounts to Delete",
                    endpoint)
        return

    # Print a message indicating that user accounts are being deleted
    general_msg("Deleting User Accounts",
                endpoint)

    # Delete each user account in the list
    for user in delete_users:
        delete_user(gconn,
                    user,
                    debug)


def create_user(gconn: object,
                user: dict,
                user_org: str,
                debug: bool = False) -> None:
    """
    Create a user in Guacamole with the given username, password, and organization.

    Args:
        gconn (object): The Guacamole connection object.
        user (dict): A dictionary containing the username and password.
        user_org (str): The organization associated with the user.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Extract the username and password from the user dictionary
    username = list(user.keys())[0]
    password = list(user.values())[0]

    # Call the create_user method of the gconn object
    response = gconn.create_user(username,
                                 password,
                                 {"guac-organization": user_org})

    # Parse the response message
    message = parse_response(response)

    # Print the appropriate message based on the response
    if message:
        info_msg(f"{message}",
                 endpoint,
                 debug)
    else:
        info_msg(f"Created User '{username}', Password '{password}'",
                 endpoint,
                 debug)
    time.sleep(0.1)


def delete_user(gconn: object,
                user: str,
                debug: bool = False) -> None:
    """
    Delete a user from the Guacamole system.

    Args:
        gconn (object): A connection object to the Guacamole system.
        user (str): The username of the user to be deleted.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Call the delete_user method of the gconn object
    response = gconn.delete_user(user)

    # Print the appropriate message based on the response
    message = parse_response(response)
    if message:
        info_msg(f"{message}",
                 endpoint,
                 debug)
    else:
        info_msg(f"Deleted Account '{user}'",
                 endpoint,
                 debug)
    time.sleep(0.1)


def create_user_conns(gconn: object,
                      create_conns: list,
                      conn_groups: dict,
                      guacd_ips: dict,
                      debug: bool = False):
    """
    Create user connections.

    Args:
        gconn (object): The gconn object.
        create_conns (list): List of connections to create.
        conn_groups (dict): Dictionary of connection groups.
        guacd_ips (dict): Dictionary of guacd servers.
        debug (bool, optional): If True, enable debug mode. Defaults to False.

    Returns:
        dict: Dictionary of created connections.
    """

    endpoint = 'Guacamole'

    # Check if there are no connections to create
    if not create_conns:
        general_msg("No User Connections to Create",
                    endpoint)
        return

    # Print a message indicating if there are guacd servers
    if guacd_ips:
        general_msg("Found Guacd servers. ",
                    endpoint)
        info_msg(guacd_ips,
                 endpoint,
                 debug)
    else:
        general_msg("No Guacd servers found",
                    endpoint)

    conns = {}
    general_msg("Creating User Connections",
                endpoint)
    # Create connections and store their ids in the conns dictionary
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
                      debug: bool = False) -> None:
    """
    Delete user connections.

    Args:
        gconn (object): The Guacamole connection object.
        delete_conn_ids (list): List of connection IDs to delete.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.
    """

    endpoint = 'Guacamole'

    # Check if there are any connection IDs to delete
    if not delete_conn_ids:
        general_msg("No User Connections to Delete",
                    endpoint)
        return

    general_msg("Deleting User Connections",
                endpoint)

    # Delete each connection ID
    for conn_id in delete_conn_ids:
        delete_conn(gconn,
                    conn_id,
                    debug)


def create_conn(gconn: object,
                conn: dict,
                conn_groups: dict,
                guacd_ips: dict,
                conn_id: str | None,
                debug: bool = False) -> None:
    """Create a user connection.

    Args:
        gconn (object): The connection object.
        conn (dict): The connection details.
        conn_groups (dict): The connection groups.
        guacd_ips (dict): The guacd IPs.
        conn_id (str | None): The connection ID.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        str: The connection ID
    """

    endpoint = 'Guacamole'

    # Extract necessary information from the connection details
    conn_proto = conn['protocol']
    conn_name = conn['name']
    conn_org = conn_name.split('.')[0]
    conn_group_id = conn_groups[conn_org]

    # Determine the type of request based on whether a connection ID is provided
    if conn_id:
        req_type = "put"
        update = True
    else:
        req_type = "post"
        update = False

    # Manage the connection using the connection object
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

    # Parse the response message
    message = parse_response(response)

    if message:
        # Handle message if present
        info_msg(f"{message}",
                 endpoint,
                 debug)
        time.sleep(0.1)
        conn_id = get_conn_id(gconn,
                              conn_name,
                              conn_group_id,
                              debug)
    elif update:
        # Print the update case
        info_msg(f"Updated User Connection '{conn_name}'. "
                 f"User '{conn['params']['username']}', "
                 f"Pass '{conn['params']['password']}', "
                 f"IP '{conn['params']['hostname']}'",
                 endpoint,
                 debug)
    else:
        # Print the create case
        info_msg(f"Created User Connection '{conn_name}'. "
                 f"User '{conn['params']['username']}', "
                 f"Pass '{conn['params']['password']}', "
                 f"IP '{conn['params']['hostname']}'",
                 endpoint,
                 debug)
        time.sleep(0.1)
        conn_id = get_conn_id(gconn,
                              conn_name,
                              conn_group_id,
                              debug)
    time.sleep(0.1)

    return conn_id


def delete_conn(gconn: object,
                conn_id: str,
                debug: bool = False) -> None:
    """
    Delete a user connection.

    Args:
        gconn (object): The guacamole connection object
        conn_id (str): The ID of the connection to be deleted
        debug (bool, optional): Whether to print debug messages. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Delete the connection using the guacamole connection object
    response = gconn.delete_connection(conn_id)

    # Parse the response to extract any error message
    message = parse_response(response)

    # If there is an error message, print it
    if message:
        info_msg(f"{message}",
                 endpoint,
                 debug)
    else:
        # If no error message, print the deleted connection ID
        info_msg(f"Deleted Connection ID '{conn_id}'",
                 endpoint,
                 debug)
    time.sleep(0.1)


def associate_user_conns(gconn: object,
                         mappings: dict,
                         org_name: str,
                         conn_groups: dict,
                         conn_ids: dict,
                         debug: bool = False) -> None:
    """
    Associate user connections with the given Guacamole connection objects.

    Args:
        gconn (object): The Guacamole connection object.
        mappings (dict): A dictionary containing user connection mappings.
        org_name (str): The name of the organization.
        conn_groups (dict): A dictionary mapping connection group names to their IDs.
        conn_ids (dict): A dictionary mapping connection names to their IDs.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Check if there are no mappings
    if not mappings:
        general_msg("No User Connections to Associate",
                    endpoint)
        return

    general_msg("Associating User Connections",
                endpoint)

    # Associate user connections for each mapping
    for mapping in mappings:
        user_name = list(mapping.keys())[0]
        conn_names = list(mapping.values())[0]
        parent_id = conn_groups[org_name]
        groups = []

        # Associate user with parent connection group
        associate_conn(gconn,
                       user_name,
                       parent_id,
                       True,
                       org_name,
                       debug)

        # Associate user with each connection group and connection
        for conn_name in conn_names:
            group = conn_name.split('.')[0]
            conn_group_id = conn_groups[group]
            # Associate user to the group if they are not already
            if group not in groups:
                groups.append(group)
                associate_conn(gconn,
                               user_name,
                               conn_group_id,
                               True,
                               group,
                               debug)
            # Associate user with connection
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
                   conn_name: str | None = None,
                   debug: bool = False) -> None:
    """
    Associates a user with a connection in Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        user_name (str): The name of the user.
        conn_id (str): The ID of the connection.
        is_group (bool): Whether the connection is a group connection.
        conn_name (str, optional): The name of the connection. Defaults to None.
        debug (bool, optional): Whether to print debug messages. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Associate the user with the group or connection
    response = gconn.update_user_connection(user_name,
                                            conn_id,
                                            "add",
                                            is_group)
    # Parse the response to extract any error message
    message = parse_response(response)

    # Handle message if present
    if message:
        info_msg(f"{message}",
                 endpoint,
                 debug)
    # Print feedback with connection name if present
    elif conn_name:
        conn_type = 'group' if is_group else 'connection'
        info_msg(f"Associated '{user_name}' to {conn_type} '{conn_name}' ({conn_id})",
                 endpoint,
                 debug)
    # Print feedback with message without connection name
    else:
        info_msg(f"Associated '{user_name}' to connection id '{conn_id}'",
                 endpoint,
                 debug)
    time.sleep(0.1)


def get_conn_group_id(gconn: object,
                      org_name: str,
                      debug: bool = False) -> str:
    """
    Retrieve the connection group ID for a given organization name.

    Args:
        gconn (object): The Guacamole connection object.
        org_name (str): The name of the organization.
        debug (bool, optional): Flag to enable debugging. Defaults to False.

    Returns:
        str: The connection group ID for the organization.

    Raises:
        IndexError: If the organization has no connection group IDs.
    """

    endpoint = 'Guacamole'

    # Retrieve the connection groups as a dictionary
    conn_groups = json.loads(gconn.list_connection_groups())

    try:
        # Find the group ID for the given organization name
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == org_name]
        return_id = group_id[0]

        # Log the retrieval of the group ID
        info_msg(f"Retrieved {org_name}'s group ID '{return_id}'",
                 endpoint,
                 debug)

    except IndexError as error:
        # Log an error if the organization has no connection group IDs
        error_msg(f"{org_name} has no connection group ID. {error}",
                  endpoint)
        return_id = None

    return return_id


def get_conn_id(gconn: object,
                conn_name: str,
                conn_group_id: str,
                debug: bool = False) -> str:
    """
    Retrieves the connection ID for a given connection name and group ID from Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        conn_name (str): The name of the connection.
        conn_group_id (str): The ID of the connection group.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        str: The connection ID.

    Raises:
        IndexError: If the connection is not found.
    """

    endpoint = 'Guacamole'

    # Retrieve the connection list
    conn_list = json.loads(gconn.list_connections())

    try:
        # Find the connection with the given name and group ID
        conn_id = [conn['identifier'] for conn in conn_list.values()
                   if conn['parentIdentifier'] == conn_group_id
                   and conn['name'] == conn_name][0]

        info_msg(f"Retrieved {conn_name}'s connection ID '{conn_id}'",
                 endpoint,
                 debug)

    except IndexError as error:
        # Handle the case when the connection is missing from the list
        error_msg(f"{conn_name} has no connection ID. {error}",
                  endpoint)
        conn_id = None

    return conn_id


def get_groups(gconn: object,
               parent_id: str,
               debug: bool = False) -> dict:
    """
    Retrieves connection groups from a Guacamole connection.

    Args:
        gconn (object): The Guacamole connection object.
        parent_id (str): The parent identifier of the connection groups.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        dict: A dictionary containing the connection groups.
    """

    endpoint = 'Guacamole'

    # Retrieve all connection groups
    all_conn_groups = json.loads(gconn.list_connection_groups())

    # Filter connection groups by parent identifier
    conn_groups = [group for group in all_conn_groups.values()
                   if group['parentIdentifier'] == parent_id]

    general_msg("Retrieved connection groups",
                endpoint)
    info_msg(conn_groups,
             endpoint,
             debug)

    return conn_groups


def get_conns(gconn: object,
              conn_group_ids: dict,
              debug: bool = False) -> dict:
    """
    Retrieves connections from Guacamole client using the provided connection group IDs.

    Args:
        gconn (object): Guacamole client object.
        conn_group_ids (dict): Dictionary of connection group IDs.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        dict: List of connections retrieved from Guacamole.
    """

    endpoint = 'Guacamole'

    # Retrieve the connections from Guacamole client
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

    # Retrieve params for each connection
    for conn in conns:
        conn['params'] = json.loads(
            gconn.detail_connection(conn['identifier'], "params")
        )

    general_msg("Retrieved connections",
                endpoint)
    info_msg(conns,
             endpoint,
             debug)
    return conns


def get_users(gconn: object,
              org_name: str,
              debug: bool = False) -> list[str]:
    """
    Retrieves a list of users from the Guacamole connection object that belong
    to a specific organization.

    Args:
        gconn (object): The Guacamole connection object.
        org_name (str): The name of the organization.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        list[str]: A list of usernames belonging to the specified organization.
    """

    endpoint = 'Guacamole'

    # Load all users from the Guacamole connection object
    all_users = json.loads(gconn.list_users())

    # Filter the users based on the organization name
    users = [user['username'] for user in all_users.values()
             if user['attributes']['guac-organization'] == org_name]

    general_msg("Retrieved users accounts",
                endpoint)
    info_msg(users,
             endpoint,
             debug)

    return users


def find_domain_name(heat_params: dict,
                     debug: bool = False) -> str:
    """
    Finds and returns the domain name from the given heat parameters.

    Args:
        heat_params (dict): The heat parameters dictionary.
        debug (bool, optional): Flag indicating whether to enable debug mode. 
            Defaults to False.

    Returns:
        str: The domain name if found, empty string otherwise.

    Raises:
        KeyError: If the domain name is not found.
    """

    endpoint = 'Guacamole'

    try:
        # Retrieve the domain name from heat parameters
        domain_name = heat_params['domain_name']['default']

    except KeyError:
        general_msg("Did not find a domain name",
                    endpoint)
        return ''

    general_msg(f"Retrieved domain name '{domain_name}'",
                endpoint)

    return domain_name


def find_group_ids(conn_list: list,
                   debug: bool = False) -> dict:
    """
    Locates the child groups and their connection ids.

    Args:
        conn_list (list): A list of connection dictionaries.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        dict: A dictionary containing the connection group IDs.
    """

    endpoint = 'Guacamole'

    # Extract the connection group IDs from the list of connections
    conn_group_ids = [
        conn['identifier']
        for conn in conn_list
    ]

    if conn_group_ids:
        general_msg("Found connection group IDs",
                    endpoint)
        info_msg(conn_group_ids,
                 endpoint,
                 debug)
    else:
        error_msg("Did not find connection group IDs",
                  endpoint)

    return conn_group_ids


def find_conn_id(conn_list: list,
                 conn_name: str,
                 conn_group_id: str,
                 debug: bool = False) -> str | None:
    """
    Find the connection ID for a given connection name and group ID in a list of connections.

    Args:
        conn_list (list): List of connections.
        conn_name (str): Name of the connection to find.
        conn_group_id (str): Group ID of the connection to find.
        debug (bool, optional): Flag indicating whether to enable debug mode. Defaults to False.

    Returns:
        str | None: The connection ID of the found connection.

    Raises:
        KeyError: If the connection name is missing from the connection list.
    """

    endpoint = 'Guacamole'

    try:
        # Find the connection ID in the connection list
        conn_id = [conn['identifier'] for conn in conn_list.values()
                   if conn['parentIdentifier'] == conn_group_id
                   and conn['name'] == conn_name][0]

    except KeyError as error:
        error_msg(f"'{conn_name}' is missing from connection list. {error}")
        return None

    if conn_id:
        info_msg(f"Found {conn_name}'s connection ID '{conn_id}'",
                 endpoint,
                 debug)
    else:
        error_msg(f"'{conn_name}' has no connection ID",
                  endpoint)

    return conn_id


def parse_response(response: object) -> str:
    """
    Parses the response object and returns the message from the JSON payload.

    Args:
        response (object): The response object containing the JSON payload.

    Returns:
        str: The message extracted from the JSON payload.

    Raises:
        json.decoder.JSONDecodeError: If the response does not contain a JSON payload.
    """

    try:
        # Extract the message from the response
        message = json.loads(response.text).get('message', '')
    except json.decoder.JSONDecodeError:
        return ''

    return message
