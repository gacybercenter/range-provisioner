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
                              {
                                  'conn_proto': guac_params['conn_proto'],
                                  'heat_user': guac_params['heat_user'],
                                  'heat_pass': guac_params['heat_pass'],
                                  'domain_name': guac_params['domain_name']
                              },
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

    delete_users, delete_group_ids = delete_data(guac_params)

    delete_conn_groups(gconn,
                       delete_group_ids,
                       debug)

    delete_user_accts(gconn,
                      delete_users,
                      debug)

    success_msg("Deprovisioned Guacamole")
    return True


def reprovision(gconn,
                guac_params,
                debug=False):
    """Reprovision Guacamole connections and users"""

    deprovision(gconn,
                guac_params,
                debug)

    provision(gconn,
              guac_params,
              debug)

    success_msg("Reprovisioned Guacamole")
    return True


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

# TODO(MCcrusade): Yeah, What he said. ^


def create_data(guac_params: dict) -> tuple:
    """Formats the data used to create Guacamole"""

    new_users = guac_params['new_users']
    new_groups = guac_params['new_groups']
    instances = guac_params['instances']

    create_groups = new_groups
    create_users = []
    create_conns = []
    mappings = []
    guacd_ips = {}

    for username, data in new_users.items():
        create_users.append({username: data['password']})
        mappings.append({username: [instance['name'] for instance in instances
                                    if instance['name'] in data['instances']]})
        conn_instances = [instance for instance in instances
                          if instance['name'] in data['instances']]
        for instance in conn_instances:
            if instance not in create_conns:
                create_conns.append(instance)

    for instance in instances:
        if "guacd" in instance['name']:
            guacd_org = instance['name'].split('.')[0]
            guacd_ips[guacd_org] = instance['public_v4']

    return ({
        'groups': create_groups,
        'users': create_users,
        'conns': create_conns,
        'mappings': mappings
    }, guacd_ips)


def delete_data(guac_params: dict) -> tuple:
    """Formats the data used to delete Guacamole"""

    conn_group_ids = guac_params['conn_group_ids']
    conn_users = guac_params['conn_users']
    # conn_list = guac_params['conn_list']

    return (conn_users,
            conn_group_ids)


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
        child_id = get_conn_group_id(gconn, child_name, debug)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Created Group: "
                     f"{child_name} under group ID: {parent_id}", debug)

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
                      conn_vars: dict,
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
                                       conn_vars,
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
                conn_vars: dict,
                conn_id: str | None,
                debug=False) -> None:
    """Create a user connection."""

    conn_proto = conn_vars['conn_proto']
    heat_user = conn_vars['heat_user']
    heat_pass = conn_vars['heat_pass']
    domain_name = conn_vars['domain_name']
    conn_name = conn['name']
    conn_org = conn_name.split('.')[0]
    conn_group_id = conn_groups[conn_org]

    conn_ip = conn['public_v4'] if conn_org not in guacd_ips.keys(
    ) else conn['private_v4']

    if conn_id:
        req_type = "put"
        update = True
    else:
        req_type = "post"
        update = False

    response = gconn.manage_connection(
        req_type, conn_proto, conn_name,
        conn_group_id, conn_id,
        {
            "hostname": conn_ip,
            "port": "3389" if conn_proto == "rdp" else "22",
            "username": heat_user,
            "password": heat_pass,
            "domain": domain_name,
            "security": "any" if conn_proto == "rdp" else "",
            "ignore-cert": "true" if conn_proto == "rdp" else ""
        },
        {
            "max-connections": "1",
            "max-connections-per-user": "1",
            "guacd-hostname": guacd_ips.get(conn_org)
        }
    )
    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    elif update:
        info_msg(f"Guacamole:  Updated User Connection: {conn_name}. "
                 f"({heat_user}, {heat_pass}) "
                 f"IP: {conn_ip}", debug)
    else:
        info_msg(f"Guacamole:  Created User Connection: {conn_name}. "
                 f"({heat_user}, {heat_pass}) "
                 f"IP: {conn_ip}", debug)
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
                 f"group ID(s): {group_id}", debug)

    except IndexError:
        error_msg(f"Guacamole ERROR:  {org_name} "
                  "has no connection group ID(s)")
        return_id = None
    return return_id


def get_child_groups(gconn: object,
                     conn_group_id: str,
                     debug=False) -> dict:
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

    all_conns = json.loads(gconn.list_connections())
    conns = [conn for conn in all_conns
             if all_conns[conn]['parentIdentifier'] in conn_group_ids]
    info_msg("Guacamole:  Retrieved connections:", debug)
    info_msg(conns, debug)
    return conns


def get_users(gconn: object,
              org_name: str,
              debug=False) -> dict:
    """Get user data from Guacamole"""

    all_users = json.loads(gconn.list_users())
    users = [user for user in all_users
                 if all_users[user]['attributes']['guac-organization'] == org_name]
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


def find_conn_group_id(conn_groups: dict,
                       org_name: str,
                       debug=False) -> str:
    """Locates the parent connection group id"""

    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == org_name]
        return_id = group_id[0]
        info_msg(f"Guacamole:  Found {org_name}'s "
                 f"group ID(s): {return_id}", debug)

    except IndexError:
        general_msg(f"Guacamole:  {org_name} "
                    "has no connection group ID(s)")
        return_id = None
    return return_id


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
