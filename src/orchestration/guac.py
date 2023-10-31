"""
Author: Marcus Corulli
Description: Provision and Deprovision Guacamole
Date: 09/28/2023
Version: 1.0

Description:
    Contains all the main functions for provisioning Guacamole
"""
import time
from orchestration.heat import get_ostack_instances
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

    conns_to_create, conns_to_delete, current_conns = create_conn_data(guac_params,
                                                                       update,
                                                                       debug)

    conn_ids = create_conns(gconn,
                            conns_to_create,
                            current_conns,
                            update,
                            debug)

    if update:
        delete_conns(gconn,
                     conns_to_delete)

    users_to_create, users_to_delete, current_users = create_user_data(guac_params,
                                                                       conn_ids,
                                                                       update,
                                                                       debug)

    create_users(gconn,
                 users_to_create,
                 current_users,
                 update,
                 debug)

    if update:
        delete_users(gconn,
                     users_to_delete)

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

    conns_to_delete, users_to_delete = delete_data(guac_params)

    delete_conns(gconn,
                 conns_to_delete)

    delete_users(gconn,
                 users_to_delete)

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
    current_conns = extract_connections(guac_params['conns'])

    conns_to_delete = []

    if update:
        create_names = [
            conn['name']
            for conn in conns_to_create
        ]
        for conn in current_conns:
            if conn['name'] not in create_names:
                conns_to_delete.append(conn)

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

    return conns_to_create, conns_to_delete, current_conns


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
    current_users = guac_params['users']

    users_to_create = []
    passwords = {}

    # Generate the create data based on the new user mapping data
    for username, data in new_users.items():
        passwords[username] = data['password']
        permissions = data['permissions']
        users_to_create.append(
            {
                'username': username,
                'attributes': {
                    'guac-organization': org_name
                },
                'permissions': {
                    'connectionPermissions': {
                        conn_ids[conn_name]: ['READ']
                        for conn_name in permissions['connectionPermissions']
                    },
                    'connectionGroupPermissions': {
                        conn_ids[conn_name]: ['READ']
                        for conn_name in permissions['connectionGroupPermissions']
                    },
                    'sharingProfilePermissions': {
                        conn_ids[conn_name]: ['READ']
                        for conn_name in permissions['sharingProfilePermissions']
                    },
                    'userPermissions': permissions['userPermissions'],
                    'userGroupPermissions': permissions['userGroupPermissions'],
                    'systemPermissions': permissions['systemPermissions']
                }
            }
        )

    users_to_delete = []

    if update:
        create_names = [
            user['username']
            for user in users_to_create
        ]
        for user in current_users:
            if user['username'] not in create_names:
                users_to_delete.append(user)

        users_to_create = remove_empty(users_to_create)
        current_users = remove_empty(current_users)

        for user in current_users:
            if user['permissions'].get('activeConnectionPermissions'):
                del user['permissions']['activeConnectionPermissions']

            if user in users_to_create:
                users_to_create.remove(user)
                general_msg(f"No changes needed for user '{user['username']}'",
                            endpoint)
                info_msg(user,
                         endpoint,
                         debug)

    for user in users_to_create:
        user['password'] = passwords[user['username']]

    return users_to_create, users_to_delete, current_users


def delete_data(guac_params: object) -> dict:
    """
    Create data for Guacamole API based on given parameters.

    Args:
        guac_params (dict): Parameters for creating the data.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        list: A dictionary containing the connection to be deleted.

    """

    conns_to_delete = [guac_params['conns']] if guac_params.get('conns') else []
    users_to_delete = guac_params['users'] if guac_params.get('users') else []

    return conns_to_delete, users_to_delete


def create_conns(gconn: object,
                 conns_to_make: dict,
                 current_conns: dict = None,
                 update: bool = False,
                 debug: bool = False) -> dict:
    """
    Create Guacamole connections

    Args:
        gconn (object): The Guacamole connection object.
        conns_to_make (dict): List of connections to create.
        current_conns (dict, optional): List of current connections.
        update (bool, optional): Whether to update connections.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        dict: A dictionary containing the connection IDs.
    """

    endpoint = 'Guacamole'
    operation = "Updated" if update else "Created"
    current_names = []
    conn_ids = {'ROOT': 'ROOT'}

    for conn in current_conns:
        current_names.append(conn['name'])
        conn_ids[conn['name']] = conn['identifier']

    if not conns_to_make:
        general_msg("There Are No New Connections",
                    endpoint)
        return conn_ids

    for conn in conns_to_make:
        conn_id = None
        if conn['name'] in current_names:
            if update:
                conn_id = conn_ids[conn['name']]
                current_names.remove(conn['name'])
            else:
                general_msg(f"Connection '{conn['name']}' already exists",
                            endpoint)
                continue
        parent_id = conn_ids[conn['parent']]
        conn_ids[conn['name']] = create_conn(gconn,
                                             parent_id,
                                             conn,
                                             conn_id,
                                             debug)

    success_msg(f"{operation} Connections",
                endpoint)

    return conn_ids


def create_conn(gconn: object,
                parent_id: str,
                conn_data: dict,
                conn_id: str | None = None,
                debug: bool = False) -> str:
    """
    Creates a Guacamole connection

    Args:
        gconn (object): The Guacamole connection object.
        parent_id (str): The parent identifier of the connection.
        conn_data (dict): The connection data.
        conn_id (str, optional): The ID of the connection.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        str: The connection ID
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
        response = gconn.manage_connection(conn_data['protocol'],
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
        conn_id = response.get('identifier')

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(
            f"{operation} {conn_type} '{conn_data['name']}' ({conn_id}) under ID '{parent_id}'",
            endpoint
        )

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
        general_msg("No Connections to Delete",
                    endpoint)
        return

    if len(conns) > 1:
        conns_to_delete = remove_children(conns)
    else:
        conns_to_delete = conns

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

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(
            f"Deleted {conn_type} ID '{conn_id}'",
            endpoint
        )
    time.sleep(0.1)


def remove_children(connections: list) -> list:
    """
    Recursively delete connection groups in Guacamole.

    Parameters:
        connections (list): A list of connection groups.

    Returns:
        list: The reduced list of connection groups to be deleted.
    """

    def find_descendants(connection: dict,
                         descendants: list) -> None:
        for child in connections:
            if (isinstance(child, dict) and
                    (child.get('parentIdentifier') == connection['identifier'] or
                     child.get('primaryConnectionIdentifier') == connection['identifier'])
                ):
                descendants.append(child)
                find_descendants(child,
                                 descendants)

    connections_to_delete = []
    for connection in connections:
        descendants = []
        find_descendants(connection,
                         descendants)
        if descendants:
            connections_to_delete.append(connection)

    return connections_to_delete


def create_users(gconn: object,
                 users_to_create: dict,
                 current_users: list | None = None,
                 update: bool = False,
                 debug: bool = False) -> dict:
    """
    Creates Guacamole users

    Args:
        gconn (object): The Guacamole connection object.
        users_to_create (dict): List of users to create.
        current_users (list | None, optional): List of current users.
        update (bool, optional): Whether to update users.
        debug (bool, optional): Whether to enable debug mode.

    Returns:
        dict: A dictionary of user objects.
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
    ] if current_users else []

    if update:
        current_user_data = {
            user['username']: user
            for user in current_users
        }

    for user in users_to_create:
        current_user = None
        if user['username'] in current_names:
            if update:
                current_user = current_user_data[user['username']]
                current_names.remove(user['username'])
            else:
                general_msg(f"User account '{user['username']}' already exists",
                            endpoint)
                continue
        create_user(gconn,
                    user,
                    current_user,
                    debug)
        update_user_conns(gconn,
                          user,
                          current_user,
                          debug)
        update_user_perms(gconn,
                          user,
                          current_user,
                          debug)

    success_msg(f"{operation} User Accounts",
                endpoint)

    return


def create_user(gconn: object,
                user: dict,
                current_user: dict | None = None,
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

    new_data = {
        'username': user['username'],
        'attributes': user.get('attributes', {})
    }
    if current_user:
        current_data = {
            'username': current_user['username'],
            'attributes': current_user.get('attributes', {})
        }
        if current_data == new_data:
            info_msg(f"No changes needed for user account '{new_data['username']}'",
                     endpoint,
                     debug)
            return

        response = gconn.update_user(new_data['username'],
                                     new_data['attributes'])
        message = f"Updated user account '{new_data['username']}'"
    else:
        response = gconn.create_user(new_data['username'],
                                     user['password'],
                                     new_data['attributes'])
        message = f"Created user account '{new_data['username']}' ({user['password']})"

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(message,
                    endpoint)

    time.sleep(0.1)

    info_msg(user.get('attributes', {}),
             endpoint,
             debug)


def update_user_conns(gconn: object,
                      user: dict,
                      current_user: dict | None = None,
                      debug: bool = False) -> None:
    """
    Updates user accounts with connection groups

    Args:
        gconn (object): The Guacamole connection object.
        user (dict): A dictionary containing the username and password.
        current_user (dict | None, optional): A dictionary containing the current user.
            Determines whether to create or update. Defaults to None.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    connection_ids = {
        'group': user['permissions']['connectionGroupPermissions'].keys()
        if user['permissions'].get('connectionGroupPermissions') else [],
        'connection': user['permissions']['connectionPermissions'].keys()
        if user['permissions'].get('connectionPermissions') else [],
        'sharing profile': user['permissions']['sharingProfilePermissions'].keys()
        if user['permissions'].get('sharingProfilePermissions') else []
    }

    if current_user:
        current_connection_ids = {
            'group': current_user['permissions']['connectionGroupPermissions'].keys()
            if current_user['permissions'].get('connectionGroupPermissions') else [],
            'connection': current_user['permissions']['connectionPermissions'].keys()
            if current_user['permissions'].get('connectionPermissions') else [],
            'sharing profile': current_user['permissions']['sharingProfilePermissions'].keys()
            if current_user['permissions'].get('sharingProfilePermissions') else []
        }
        connection_ids, remove_ids = get_id_difference(connection_ids,
                                                       current_connection_ids)

        for conn_type, conn_ids in remove_ids.items():
            if not conn_ids:
                info_msg(
                    f"No {conn_type} permissions to remove from '{user['username']}'",
                    endpoint,
                    debug
                )
                continue
            update_user_conn(gconn,
                             user['username'],
                             conn_ids,
                             conn_type,
                             'remove')

    for conn_type, conn_ids in connection_ids.items():
        if not conn_ids:
            info_msg(
                f"No {conn_type} permissions to add to '{user['username']}'",
                endpoint,
                debug
            )
            continue
        conn_ids = list(conn_ids)
        update_user_conn(gconn,
                         user['username'],
                         conn_ids,
                         conn_type,
                         'add')


def update_user_conn(gconn: object,
                     user: dict | str,
                     conn_ids: list,
                     conn_type: str = 'connection',
                     operation: str = 'add') -> None:
    """
    Updates user accounts with connection groups

    Args:
        gconn (object): The Guacamole connection object.
        user (dict | str): A dictionary or string containing the username
        conn_ids (list): A list of connection IDs.
        conn_type (str, optional): The type of connection. Defaults to 'connection'.
        operation (str, optional): The operation to perform. Defaults to 'add'.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    if isinstance(user, dict):
        user = user['username']

    if conn_type not in ['group', 'connection', 'sharing profile']:
        error_msg(
            f"Invalid connection type '{conn_type}'",
            endpoint
        )
        general_msg(
            "Use 'group', 'connection', or 'sharing profile'",
            endpoint
        )
        return

    if operation not in ['add', 'remove']:
        error_msg(
            f"Invalid connection operation '{operation}'",
            endpoint
        )
        general_msg(
            "Use 'add' or 'remove'",
            endpoint
        )
        return

    action = 'Added' if operation == 'add' else 'Removed'

    response = gconn.update_connection_permissions(user,
                                                   conn_ids,
                                                   operation,
                                                   conn_type)

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(f"{action} '{user}' {conn_type} permissions",
                    endpoint)
    time.sleep(0.1)


def update_user_perms(gconn: object,
                      user: dict,
                      current_user: dict | None = None,
                      debug: bool = False) -> None:
    """
    Updates user accounts with connection groups

    Args:
        gconn (object): The Guacamole connection object.
        user (dict): A dictionary containing the username and password.
        current_user (dict | None, optional): A dictionary containing the current user.
            Determines whether to create or update. Defaults to None.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    system_perms = user['permissions'].get('systemPermissions', [])

    if current_user:
        current_system_perms = current_user['permissions'].get(
            'systemPermissions', [])
        remove_system_perms = list(
            filter(
                lambda x: x not in system_perms, current_system_perms
            )
        )
        system_perms = list(
            filter(
                lambda x: x not in current_system_perms, system_perms
            )
        )

        if not remove_system_perms:
            info_msg(
                f"No system permissions to remove from '{user['username']}'",
                endpoint,
                debug
            )
        else:
            update_user_perm(gconn,
                             user,
                             remove_system_perms,
                             'remove')

    if not system_perms:
        info_msg(
            f"No system permissions to add to '{user['username']}'",
            endpoint,
            debug
        )
        return
    update_user_perm(gconn,
                     user,
                     system_perms,
                     'add')


def update_user_perm(gconn: object,
                     user: dict | str,
                     system_perms: list,
                     operation: str = 'add') -> None:
    """
    Updates user accounts with connection groups

    Args:
        gconn (object): The Guacamole connection object.
        user (dict): A dictionary containing the username and password.
        conn_ids (list): A list of connection IDs.
        conn_type (str, optional): The type of connection. Defaults to 'connection'.
        operation (str, optional): The operation to perform. Defaults to 'add'.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    if isinstance(user, dict):
        user = user['username']

    if operation not in ['add', 'remove']:
        error_msg(
            f"Invalid connection operation '{operation}'",
            endpoint
        )
        general_msg(
            "Use 'add' or 'remove'",
            endpoint
        )
        return

    action = 'Added' if operation == 'add' else 'Removed'

    response = gconn.update_user_permissions(user,
                                             system_perms,
                                             operation)

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(f"{action} '{user}' system permissions {system_perms}",
                    endpoint)
    time.sleep(0.1)


def delete_users(gconn: object,
                 users_to_delete: list) -> None:
    """
    Delete user accounts

    Args:
        gconn (object): The Guacamole connection object.
        delete_users (list): A list of user accounts to delete.

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

    Returns:
        None
    """

    endpoint = 'Guacamole'

    if isinstance(user, dict):
        user = user['username']

    response = gconn.delete_user(user)

    if isinstance(response, dict) and response.get('message'):
        general_msg(response['message'],
                    endpoint)
    else:
        general_msg(f"Deleted user account '{user}'",
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
        groups = gconn.list_connection_groups().values()
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
        conns = gconn.list_connections().values()
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
        sharings = gconn.list_sharing_profile().values()
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
    conn_groups = gconn.detail_connection_group_connections(parent_id)

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
        for user in gconn.list_users().values()
        if user['attributes']['guac-organization'] == org_name
    ]

    if not users:
        general_msg("There are no current user accounts",
                    endpoint)
        return []

    for user in users:
        user['permissions'] = gconn.detail_user_permissions(user['username'])
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
                conn['parameters'] = gconn.detail_connection(conn['identifier'],
                                                             "parameters")
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

    return conns


def get_id_difference(connection_ids: dict,
                      current_connection_ids: dict) -> (dict, dict):
    """
    Gets the difference between two connection ids.

    Parameters:
        connection_ids (dict): The current connection ids.
        current_connection_ids (dict): The new connection ids.

    Returns:
        (dict, dict): The added and removed connection ids.
    """

    added_ids = {}
    removed_ids = {}

    for category in connection_ids:
        added_ids[category] = list(
            set(connection_ids[category]) -
            set(current_connection_ids[category])
        )
        removed_ids[category] = list(
            set(current_connection_ids[category]) -
            set(connection_ids[category])
        )

    return added_ids, removed_ids


def get_heat_instances(conn: object,
                       guac_params: dict,
                       debug: bool = False) -> list:
    """
    Get the stack instances from heat

    Parameters:
        conn (object): The guacamole connection.
        guac_params (dict): The guacamole parameters.
        debug (bool): The debug flag. Defaults to False.

    Returns:
        list: The stack instances.
    """

    endpoint = 'Guacamole'

    ostack_complete = False
    while not ostack_complete:
        instances = get_ostack_instances(conn,
                                         guac_params['new_groups'],
                                         debug)
        for instance in instances:
            if not instance['hostname']:
                general_msg(f"Waiting for '{instance['name']}' to get an IP address",
                            endpoint)
                time.sleep(5)
                continue
        ostack_complete = True

    return instances


def reduce_heat_instances(guac_params: dict,
                          debug: bool = False) -> list:
    """
    Get the stack instances from heat

    Parameters:
        conn (object): The guacamole connection.
        instances (dict): The openstack.
        debug (bool): The debug flag. Defaults to False.

    Returns:
        list: The stack instances.
    """

    endpoint = 'Guacamole'

    new_users = guac_params['new_users']
    instances = guac_params['instances']

    mapped_instances = []
    for data in new_users.values():
        mapped_instances.extend(
            data['permissions'].get('connectionPermissions')
        )
    mapped_instances = set(mapped_instances)

    instances = [
        instance
        for instance in instances
        if instance['name'] in mapped_instances
        or 'guacd' in instance['name']
    ]

    general_msg("Removed unmapped instances",
                endpoint)
    info_msg(instances,
             endpoint,
             debug)

    return instances
