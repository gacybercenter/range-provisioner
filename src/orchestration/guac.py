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
              update: bool = False,
              debug: bool = False) -> bool:
    """
    Provisions Guacamole with the given parameters.

    Args:
        gconn (object): Connection to the Guacamole server.
        guac_params (dict): Parameters for provisioning Guacamole.
        update (bool, optional): Whether to update existing connections and users.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    general_msg("Provisioning Guacamole",
                endpoint)

    conns_to_make, current_conns = create_conn_data(guac_params,
                                                    update,
                                                    debug)

    conn_ids = create_conns(gconn,
                            conns_to_make,
                            current_conns,
                            update,
                            debug)

    users_to_create, current_users = create_user_data(guac_params,
                                                    conn_ids,
                                                    update,
                                                    debug)

    create_users(gconn,
                 users_to_create,
                 current_users,
                 update,
                 debug)

    success_msg("Provisioned Guacamole",
                endpoint)


def deprovision(gconn: object,
                guac_params: dict) -> bool:
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

    delete_conn(gconn,
                guac_params['conns'])

    delete_users(gconn,
                 guac_params['users'])

    success_msg("Deprovisioned Guacamole",
                endpoint)


def create_conn_data(guac_params: dict,
                     update: bool = False,
                     debug: bool = False) -> tuple:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        tuple: A tuple containing the create data and the Guacd IPs.
    """

    endpoint = 'Guacamole'

    # Extract parameters from guac_params
    org_name = guac_params['org_name']
    new_groups = guac_params['new_groups']
    instances = guac_params['instances']
    recording = guac_params['recording']
    sharing = guac_params['sharing']
    current_object = guac_params['conns']

    if sharing and sharing not in ['read', 'write']:
        error_msg(
            f"The Guacamole sharing parameter is set to '{sharing}'",
            endpoint
        )
        general_msg(
            "It must be either 'read', 'write', or 'False'",
            endpoint
        )

    guacd_ips = {}

    # Filter instances by guacd
    for instance in instances.copy():
        if "guacd" in instance['name']:
            guacd_org = instance['name'].split('.')[0]
            guacd_ips[guacd_org] = instance['hostname']
            instances.remove(instance)

    conn_objects = []

    # Process each instance
    for instance in instances:
        group = instance['name'].split('.')[0]
        conn_objects.append({
            'name': instance['name'],
            'protocol': guac_params['protocol'],
            'attributes': {
                'max-connections': '1',
                'max-connections-per-user': '1',
                'guacd-hostname': guacd_ips.get(group, '')
            },
            'sharingProfiles': {
                'attributes': {},
                'name': f"{instance['name']}.{sharing}",
                'parameters': {
                    "read-only": 'true'
                } if sharing == 'read' else {}
            },
            'parameters': {
                'hostname': instance['hostname'],
                'username': guac_params['username'],
                'password': guac_params['password'],
                "domain": guac_params['domain_name'],
                "port": "3389" if guac_params['protocol'] == "rdp" else "22",
                "security": "any" if guac_params['protocol'] == "rdp" else "",
                "ignore-cert": "true" if guac_params['protocol'] == "rdp" else "",
                "enable-wallpaper": "true" if guac_params['protocol'] == "rdp" else "",
                "enable-theming": "true" if guac_params['protocol'] == "rdp" else "",
                "create-recording-path": "true" if recording else "",
                "recording-name": "${GUAC_USERNAME}-${GUAC_DATE}-${GUAC_TIME}" if recording else "",
                "recording-path": "${HISTORY_PATH}/${HISTORY_UUID}" if recording else "",
            }
        })

    # Generate the create data
    create_object = {
        'name': org_name,
        'type': 'ORGANIZATIONAL',
        'childConnectionGroups': [
            {
                'name': group,
                'type': 'ORGANIZATIONAL',
                'childConnections': [
                    conn
                    for conn in conn_objects
                    if conn['name'].split('.')[0] == group
                ],
                'attributes': {
                    'max-connections': '50',
                    'max-connections-per-user': '10'
                }
            }
            for group in new_groups
        ],
        'attributes': {
            'max-connections': '50',
            'max-connections-per-user': '10'
        }
    } if org_name != new_groups[0] else {
        'name': org_name,
        'type': 'ORGANIZATIONAL',
        'childConnections': conn_objects,
        'attributes': {
            'max-connections': '50',
            'max-connections-per-user': '10'
        }
    }

    conns_to_create = extract_connections(create_object)
    current_conns = extract_connections(current_object)

    if update:
        conns_to_create = remove_empty(conns_to_create)
        compare_conns = remove_empty(current_conns)
        for conn in compare_conns:
            del conn['identifier']
            if conn.get('parentIdentifier'):
                del conn['parentIdentifier']
            if conn.get('primaryConnectionIdentifier'):
                del conn['primaryConnectionIdentifier']

            if conn in conns_to_create:
                conns_to_create.remove(conn)
                general_msg(f"No changes needed for connection '{conn['name']}'",
                            endpoint)
                info_msg(conn,
                         endpoint,
                         debug)

    return conns_to_create, current_conns


def create_user_data(guac_params: dict,
                     conn_ids: dict,
                     update: bool = False,
                     debug: bool = False) -> tuple:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        tuple: A tuple containing the create data and the Guacd IPs.
    """

    endpoint = 'Guacamole'

    # Extract parameters from guac_params
    org_name = guac_params['org_name']
    new_users = guac_params['new_users']
    sharing = guac_params['sharing']
    current_users = guac_params['users']

    users_to_create = []
    passwords = {}

    # Generate the create data based on the new user mapping data
    for username, data in new_users.items():
        passwords[username] = data['password']
        groups = {}
        instances = {}
        sharings = {}
        org_id = conn_ids.get(org_name)
        if org_id:
            groups[org_id] = ['READ']
        for instance in data['instances']:
            group = instance.split('.')[0]
            group_id = conn_ids.get(group)
            conn_id = conn_ids.get(instance)
            sharing_id = conn_ids.get(f"{instance}.{sharing}")
            if group_id:
                groups[group_id] = ['READ']
            if conn_id:
                instances[conn_id] = ['READ']
            if sharing_id:
                sharings[sharing_id] = ['READ']

        users_to_create.append(
            {
                'username': username,
                'attributes': {
                    'guac-organization': org_name
                },
                'permissions': {
                    'connectionPermissions': instances,
                    'connectionGroupPermissions': groups,
                    'sharingProfilePermissions': sharings
                }
            }
        )

    if update:
        users_to_create = remove_empty(users_to_create)
        compare_users = remove_empty(current_users)
        for user in compare_users:
            if user['permissions'].get('activeConnectionPermissions'):
                del user['permissions']['activeConnectionPermissions']
            if user['permissions'].get('userPermissions'):
                del user['permissions']['userPermissions']
            if user['permissions'].get('userGroupPermissions'):
                del user['permissions']['userGroupPermissions']
            if user['permissions'].get('systemPermissions'):
                del user['permissions']['systemPermissions']

            if user in users_to_create:
                users_to_create.remove(user)
                general_msg(f"No changes needed for user '{user['username']}'",
                            endpoint)
                info_msg(user,
                         endpoint,
                         debug)

    for user in users_to_create:
        user['password'] = passwords[user['username']]

    return users_to_create, current_users


def delete_conn_data(guac_params: object) -> dict:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        list: A dictionary containing the connection to be deleted.

    """

    # Get the group IDs, users, and connections to be deleted
    current_conns = guac_params['conns']

    return [current_conns]


def delete_user_data(guac_params: object) -> dict:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.

    Returns:
        dict: A dictionary containing the users to be deleted.

    """

    # Get the group IDs, users, and connections to be deleted
    current_users = guac_params['users']

    usernames = [
        user['username']
        for user in current_users
    ]

    return usernames


def create_conns(gconn: object,
                 conns_to_make: dict,
                 current_conns: dict = None,
                 update: bool = False,
                 debug: bool = False) -> dict:
    """
    Create connections
    """

    endpoint = 'Guacamole'
    operation = "Updated" if update else "Created"
    current_names = []
    conn_ids = {'ROOT': 'ROOT'}

    for conn in current_conns:
        current_names.append(conn['name'])
        conn_ids[conn['name']] = conn['identifier']

    if not conns_to_make:
        general_msg("There are no new connections",
                    endpoint)
        return conn_ids

    for conn in conns_to_make:
        if conn['name'] in current_names:
            if update:
                parent_id = conn_ids[conn['parent']]
                conn_id = conn_ids[conn['name']]
                create_conn(gconn,
                            parent_id,
                            conn,
                            conn_id,
                            debug)
                current_names.remove(conn['name'])
            else:
                general_msg(f"Connection '{conn['name']}' already exists",
                            endpoint)
            continue
        parent_id = conn_ids[conn['parent']]
        conn_ids[conn['name']] = create_conn(gconn,
                                             parent_id,
                                             conn,
                                             None,
                                             debug)
    if update:
        residual_conns = [
            conn
            for conn in current_conns
            if conn['name'] in current_names
        ]
        delete_conns(gconn,
                     residual_conns)

    success_msg(f"{operation} Connections",
                endpoint)

    return conn_ids


def create_conn(gconn: object,
                parent_id: str,
                conn_data: dict,
                conn_id: str | None = None,
                debug: bool = False) -> str:
    """
    Create connections
    """

    endpoint = 'Guacamole'
    operation = "Updated" if conn_id else "Created"

    if conn_data.get('type'):
        conn_type = "group"
    elif conn_data.get('protocol'):
        conn_type = "connection"
    else:
        conn_type = "sharing profile"

    if conn_type == "group":
        if conn_id:
            response = gconn.update_connection_group(conn_id,
                                                     conn_data['name'],
                                                     conn_data['type'],
                                                     parent_id,
                                                     conn_data.get('attributes', {}))
        else:
            response = gconn.create_connection_group(conn_data['name'],
                                                     conn_data['type'],
                                                     parent_id,
                                                     conn_data.get('attributes', {}))
    elif conn_type == "connection":
        req_type = "put" if conn_id else "post"
        response = gconn.manage_connection(req_type,
                                           conn_data['protocol'],
                                           conn_data['name'],
                                           parent_id,
                                           conn_id,
                                           conn_data.get('parameters', {}),
                                           conn_data.get('attributes', {}))
    else:
        if conn_id:
            response = gconn.update_sharing_profile(parent_id,
                                                    conn_data['name'],
                                                    conn_id,
                                                    conn_data.get('parameters', {}))
        else:
            response = gconn.create_sharing_profile(parent_id,
                                                    conn_data['name'],
                                                    conn_data.get('parameters', {}))
    time.sleep(0.1)

    if not conn_id:
        conn_id = response.json().get('identifier')

    message = f"{operation} {conn_type} '{conn_data['name']}' ({conn_id}) under ID '{parent_id}'"
    response_message(response,
                     message,
                     endpoint)
    info_msg(conn_data,
             endpoint,
             debug)

    return conn_id


def delete_conns(gconn: object,
                 conns: list) -> None:
    """
    Delete connection groups in Guacamole.

    Args:
        gconn (object): The connection object.
        conn_ids (list): List of group IDs to delete.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Check if there are no connections to delete
    if not conns:
        general_msg("No Connection Groups to Delete",
                    endpoint)
        return

    conns_to_delete = remove_children(conns)

    # Iterate over the connections and delete each connection
    for conn in conns_to_delete:
        delete_conn(gconn,
                    conn)

    success_msg("Deleted Connection Groups",
                endpoint)


def delete_conn(gconn: object,
                conn: dict | str,
                conn_type: str = 'group') -> None:
    """
    Deletes a connection group from Guacamole.

    Args:
        gconn (object): The connection object for interacting with Guacamole.
        conn (dict | str): The object or ID of the connection to be deleted.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    if isinstance(conn, dict):
        conn_id = conn['identifier']
        if conn.get('type'):
            conn_type = "group"
        elif conn.get('protocol'):
            conn_type = "connection"
        else:
            conn_type = "sharing profile"
    elif isinstance(conn, str):
        conn_id = conn
    else:
        error_msg(f"Invalid connection object: {type(conn)}",
                  endpoint)
        return

    # Delete the connection group
    if conn_type == "group":
        response = gconn.delete_connection_group(conn_id)
    elif conn_type == "connection":
        response = gconn.delete_connection(conn_id)
    elif conn_type == "sharing profile":
        response = gconn.delete_sharing_profile(conn_id)
    else:
        error_msg(f"Invalid connection type: {conn_type}",
                  endpoint)
        return

    message = f"Deleted {conn_type} ID '{conn_id}'"
    response_message(response,
                     message,
                     endpoint)
    time.sleep(0.1)


def remove_children(connections: list) -> list:
    """
    Recursively delete connection groups in Guacamole.

    Parameters:
        connections (list): A list of connection groups.

    Returns:
        list: The reduced list of connection groups to be deleted.
    """

    def find_descendants(connection: dict, descendants: list) -> None:
        for child in connections:
            if (
                child.get('parentIdentifier') == connection['identifier']
                or child.get('primaryConnectionIdentifier') == connection['identifier']
            ):
                descendants.append(child)
                find_descendants(child, descendants)

    connections_to_delete = []
    for connection in connections:
        descendants = []
        find_descendants(connection, descendants)
        if descendants:
            connections_to_delete.append(connection)

    return connections_to_delete


def create_users(gconn: object,
                 users_to_create: dict,
                 current_users: dict = None,
                 update: bool = False,
                 debug: bool = False) -> dict:
    """
    Create users
    """

    endpoint = 'Guacamole'
    operation = "Updated" if update else "Created"

    if not users_to_create:
        general_msg("There are no new users",
                    endpoint)
        return

    current_names = [
        user['username']
        for user in current_users
    ]

    for user in users_to_create:
        if user['username'] in current_names:
            if update:
                create_user(gconn,
                            user,
                            True,
                            debug)
                current_names.remove(user['username'])
            else:
                general_msg(f"User account '{user['username']}' already exists",
                            endpoint)
            continue
        create_user(gconn,
                    user,
                    False,
                    debug)

    if update:
        delete_users(gconn,
                     current_names)

    success_msg(f"{operation} User Accounts",
                endpoint)

    return


def create_user(gconn: object,
                user: dict,
                update: bool = False,
                debug: bool = False) -> None:
    """
    Create a user in Guacamole with the given username, password, and organization.

    Args:
        gconn (object): The Guacamole connection object.
        user (dict): A dictionary containing the username and password.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'
    operation = "Updated" if update else "Created"

    if update:
        response = gconn.update_user(user['username'],
                                     user.get('attributes', {}))
    else:
        response = gconn.create_user(user['username'],
                                     user['password'],
                                     user.get('attributes', {}))
    time.sleep(0.1)
    message = f"{operation} user account '{user['username']}' ({user['password']})"
    response_message(response,
                     message,
                     endpoint)
    info_msg(user,
             endpoint,
             debug)

    connection_ids = {
        'group': user['permissions']['connectionGroupPermissions'].keys(),
        'connection': user['permissions']['connectionPermissions'].keys(),
        'sharing profile': user['permissions']['sharingProfilePermissions'].keys()
    }

    for conn_type, conn_ids in connection_ids.items():
        for conn_id in conn_ids:
            response = gconn.update_user_connection(user['username'],
                                                    conn_id,
                                                    'add',
                                                    conn_type)
            time.sleep(0.1)
            message = f"Associated user '{user['username']}' with {conn_type} '{conn_id}'"
            response_message(response,
                             message,
                             endpoint)


def delete_users(gconn: object,
                 users_to_delete: list) -> None:
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
    if not users_to_delete:
        general_msg("No User Accounts to Delete",
                    endpoint)
        return

    # Delete each user account in the list
    for user in users_to_delete:
        delete_user(gconn,
                    user)

    success_msg("Deleted User Accounts",
                endpoint)


def delete_user(gconn: object,
                user: dict | str) -> None:
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

    if isinstance(user, dict):
        user = user['username']

    # Call the delete_user method of the gconn object
    response = gconn.delete_user(user)

    # Print the appropriate message based on the response
    message = f"Deleted user account '{user}'"
    response_message(response,
                     message,
                     endpoint)
    time.sleep(0.1)


def get_conn_id(gconn: object,
                conn_name: str,
                parent_id: str,
                conn_type: str = 'any',
                debug: bool = False) -> str | None:
    """
    Retrieves the connection ID for a given connection name and group ID from Guacamole.

    Args:
        gconn (object): The Guacamole connection object.
        conn_name (str): The name of the connection.
        conn_group_id (str): The ID of the connection group.
        conn_type (str, optional): The type of connection. Defaults to 'any'.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        str: The connection ID. If the connection is not found, None is returned.

    """

    endpoint = 'Guacamole'

    if conn_type not in ['any', 'group', 'connection', 'sharing profile']:
        error_msg(f"Invalid connection type '{conn_type}'",
                  endpoint)
        return None

    if conn_type in ['any', 'group']:
        groups = json.loads(gconn.list_connection_groups()).values()
        for group in groups:
            # Find the group with the given name and parent ID
            if (group['parentIdentifier'] == parent_id and
                    group['name'] == conn_name):
                conn_id = group['identifier']
                info_msg(f"Retrieved {conn_name}'s {conn_type} ID '{conn_id}'",
                         endpoint,
                         debug)
                return conn_id

    if conn_type in ['any', 'connection']:
        conns = json.loads(gconn.list_connections()).values()
        for conn in conns:
            # Find the connection with the given name and parent ID
            if (conn['parentIdentifier'] == parent_id and
                    conn['name'] == conn_name):
                conn_id = conn['identifier']
                info_msg(f"Retrieved {conn_name}'s {conn_type} ID '{conn_id}'",
                         endpoint,
                         debug)
                return conn_id

    if conn_type in ['any', 'sharing profile']:
        sharings = json.loads(gconn.list_sharing_profile()).values()
        for sharing in sharings:
            # Find the connection with the given name and parent ID
            if (sharing['primaryConnectionIdentifier'] == parent_id and
                    sharing['name'] == conn_name):
                conn_id = sharing['identifier']
                info_msg(f"Retrieved {conn_name}'s {conn_type} ID '{conn_id}'",
                         endpoint,
                         debug)
                return conn_id

    general_msg(
        f"{conn_name} has no connection ID under '{parent_id}'",
        endpoint
    )

    return None


def get_conns(gconn: object,
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

    if not parent_id:
        general_msg("There are no current connections",
                    endpoint)
        return {}

    # Filter connection groups by parent identifier
    conn_groups = json.loads(
        gconn.details_connection_group_connections(parent_id)
    )

    conn_groups = detail_conns(gconn,
                               conn_groups)

    general_msg("Retrieved current connections",
                endpoint)
    info_msg(conn_groups,
             endpoint,
             debug)

    return conn_groups


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

    # Filter the users based on the organization name
    users = [
        user
        for user in json.loads(gconn.list_users()).values()
        if user['attributes']['guac-organization'] == org_name
    ]

    if not users:
        general_msg("There are no current user accounts",
                    endpoint)
        return []

    for user in users:
        user['permissions'] = json.loads(
            gconn.detail_user_permissions(user['username'])
        )
        time.sleep(0.1)

    general_msg("Retrieved current users accounts",
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
        info_msg("Did not find a domain name",
                 endpoint,
                 debug)
        return ''

    general_msg(f"Retrieved domain name '{domain_name}'",
                endpoint)

    return domain_name


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


def response_message(response: object,
                     default='',
                     endpoint='') -> None:
    """
    Generate a response message based on the given response object.

    Parameters:
        response (object): The response object.
        default (str, optional): The default message to print if the response is empty.
            Defaults to ''.
        endpoint (str, optional): The endpoint to include in the message.
            Defaults to ''.
        debug (bool, optional): Whether to enable debug mode.
            Defaults to False.

    Returns:
        None: This function does not return anything.
    """
    # Parse the response message
    message = parse_response(response)
    # Print the appropriate message based on the response
    if message:
        general_msg(message,
                    endpoint)
    # Print the default message
    elif default:
        general_msg(default,
                    endpoint)


def remove_empty(obj: object) -> object:
    """
    Recursively removes None and empty values from a dictionary or a list.

    obj:
    dictionary (dict or list): The dictionary or list to remove None and empty values from.

    Returns:
    dict or list: The dictionary or list with None and empty values removed.
    """
    if isinstance(obj, dict):
        return {
            key: remove_empty(value)
            for key, value in obj.items()
            if value
        }
    if isinstance(obj, list):
        return [
            remove_empty(item)
            for item in obj
            if item
        ]

    return obj


def detail_conns(gconn: object,
                 obj: object) -> (object, dict):
    """
    Recursively removes None and empty values from a dictionary or a list.

    Parameters:
    obj (dict or list): The dictionary or list to remove None and empty values from.

    Returns:
    (object, dict): The modified dictionary or list and the current_conns variable.
    """
    if isinstance(obj, dict):
        if obj.get('childConnections'):
            for conn in obj['childConnections']:
                conn['parameters'] = json.loads(
                    gconn.detail_connection(conn['identifier'],
                                            "params")
                )
        return {
            key: detail_conns(gconn,
                              value)
            for key, value in obj.items()
            if value
        }

    if isinstance(obj, list):
        return [
            detail_conns(gconn,
                         item)
            for item in obj
            if item
        ]

    return obj


def extract_connections(obj: dict,
                        parent='ROOT') -> (list, dict):
    """
    Recursively walks through an object and extracts connection groups,
    connections, and sharing groups.

    Parameters:
    obj (dict): The object to extract groups and connections from.

    Returns:
    list: The extracted connection groups, connections, and sharing groups.
    """

    conns = []

    if isinstance(obj, dict):
        if obj.get('name'):
            conn = obj.copy()
            conn['parent'] = parent
            if conn.get('childConnectionGroups'):
                del conn['childConnectionGroups']
            elif conn.get('childConnections'):
                del conn['childConnections']
            elif conn.get('sharingProfiles'):
                del conn['sharingProfiles']
            conns.append(conn)
            parent = obj['name']

        for value in obj.values():
            if isinstance(value, (dict, list)):
                child_conns = extract_connections(value,
                                                  parent)
                conns.extend(child_conns)

    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                child_conns = extract_connections(item,
                                                  parent)
                conns.extend(child_conns)

    conns.sort(key=lambda x: x.get('parent'))

    return conns
