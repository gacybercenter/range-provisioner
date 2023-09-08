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
    conn_group_id = guac_params['conn_group_id']
    conn_vars = {
        'conn_proto': guac_params['conn_proto'],
        'heat_user': guac_params['heat_user'],
        'heat_pass': guac_params['heat_pass'],
        'domain_name': guac_params['domain_name']
    }

    create_vars, guacd_ips = create_data(guac_params)

    conn_groups = create_conn_groups(gconn,
                                     create_vars['groups'],
                                     conn_group_id,
                                     org_name,
                                     debug)

    create_user_accts(gconn,
                      create_vars['users'],
                      org_name,
                      debug)

    create_user_conns(gconn,
                      create_vars['conns'],
                      conn_groups,
                      guacd_ips,
                      conn_vars,
                      debug)

    associate_user_conns(gconn,
                         create_vars['conns'],
                         conn_groups,
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

    org_name = guac_params['org_name']
    conn_group_id = guac_params['conn_group_id']
    conn_vars = {
        'conn_proto': guac_params['conn_proto'],
        'heat_user': guac_params['heat_user'],
        'heat_pass': guac_params['heat_pass'],
        'domain_name': guac_params['domain_name']
    }

    update_vars, guacd_ips = update_data(guac_params)

    conn_groups = update_conn_groups(gconn,
                                     update_vars['groups'],
                                     conn_group_id,
                                     org_name,
                                     debug)

    update_user_accts(gconn,
                      update_vars['users'],
                      org_name,
                      debug)

    update_user_conns(gconn,
                      update_vars['conns'],
                      conn_groups,
                      guacd_ips,
                      conn_vars,
                      debug)

    associate_user_conns(gconn,
                         update_vars['conns']['create'] +
                         update_vars['conns']['update'],
                         conn_groups,
                         debug)

    success_msg("Reprovisioned Guacamole")
    return True


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

# TODO(MCcrusader): Yeah, What he said. ^


def create_data(guac_params) -> tuple:
    """Formats the data used to create Guacamole"""

    instances = guac_params['instances']
    new_users = guac_params['new_users']
    new_conns = guac_params['new_users']
    new_groups = guac_params['new_groups']

    create_groups = new_groups
    create_users = []
    create_conns = []
    guacd_ips = {}

    for instance in instances:
        name = instance['name']
        if name in new_conns.keys():
            create_conns.append(instance)
        if name in new_users.keys():
            instance['password'] = new_users.get(name)
            create_users.append(instance)
        if "guacd" in name:
            guacd_org = name.split('.')[0]
            guacd_ips[guacd_org] = instance['public_v4']

    return ({
        'groups': create_groups,
        'users': create_users,
        'conns': create_conns
    }, guacd_ips)


def delete_data(guac_params) -> tuple:
    """Formats the data used to delete Guacamole"""

    new_users = guac_params['new_users']
    child_groups = guac_params['child_groups']
    delete_users = list(new_users.keys())
    delete_group_ids = list(child_groups.values())

    return (delete_users,
            delete_group_ids)


def update_data(guac_params) -> tuple:
    """Formats the data used to update Guacamole"""

    instances = guac_params['instances']
    new_users = guac_params['new_users']
    new_conns = guac_params['new_users']
    new_groups = guac_params['new_groups']
    child_groups = guac_params['child_groups']
    conn_groups = guac_params['conn_groups']
    conn_list = guac_params['conn_list']
    conn_users = guac_params['conn_users']
    conn_group_id = guac_params['conn_group_id']
    # user_org = guac_params['org_name']

    create_groups = []
    create_users = []
    create_conns = []
    update_groups = []
    update_users = []
    update_conns = []
    guacd_ips = {}

    group_ids = list(child_groups.values())

    current_groups = [group['name'] for group in conn_groups.values()
                      if group['parentIdentifier'] == conn_group_id]

    current_users = [user['username'] for user in conn_users.values()
                     if user['username'].split('.')[0] in current_groups]
                    #  or user['guac_org'] == user_org]

    current_conns = [conn['name'] for conn in conn_list.values()
                     if conn['parentIdentifier'] in group_ids]

    for group in new_groups:
        if group in current_groups:
            update_groups.append(group)
        else:
            create_groups.append(group)

    for instance in instances:
        name = instance['name']
        if name in new_conns.keys():
            if name in current_conns:
                update_conns.append(instance)
            else:
                create_conns.append(instance)
        if name in new_users.keys():
            instance['password'] = new_users.get(name)
            if name in current_users:
                update_users.append(instance)
            else:
                create_users.append(instance)
        if "guacd" in name:
            guacd_org = name.split('.')[0]
            guacd_ips[guacd_org] = instance['public_v4']

    delete_group_ids = [group[1] for group in child_groups.items()
                        if group[0] not in new_groups]

    delete_users = [user for user in current_users if user not in new_users]

    delete_conn_ids = [conn['identifier'] for conn in conn_list.values()
                       if conn['parentIdentifier'] in group_ids
                       and conn['parentIdentifier'] not in delete_group_ids
                       and conn['name'] not in new_conns]

    return ({
        'groups': {
            'create': create_groups,
            'delete': delete_group_ids,
            'update': update_groups
        },
        'users': {
            'create': create_users,
            'delete': delete_users,
            'update': update_users
        },
        'conns': {
            'create': create_conns,
            'delete': delete_conn_ids,
            'update': update_conns
        }
    }, guacd_ips)


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
        guac_user_name = user['name']
        guac_user_password = user['password']
        time.sleep(0.1)
        response = gconn.create_user(guac_user_name, guac_user_password,
                                     {"guac-organization": user_org})
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg(f"Guacamole:  Created User: {guac_user_name}, "
                     f"Password: {guac_user_password}", debug)


def update_user_accts(gconn: object,
                      user_params: dict,
                      user_org: str,
                      debug=False) -> None:
    """Updates user accounts based on a lists of instances"""

    create_users = user_params['create']
    delete_users = user_params['delete']
    update_users = user_params['update']

    delete_user_accts(gconn,
                      delete_users,
                      debug)

    create_user_accts(gconn,
                      create_users,
                      user_org,
                      debug)

    if not update_users:
        general_msg("No Users Accounts to Update")
        return

    general_msg("Guacamole:  Updating User Accounts")
    for user in update_users:
        guac_user_name = user['name']
        guac_user_password = user['password']
        response = gconn.update_user(guac_user_name,
                                     {"guac-organization": user_org})
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg(f"Guacamole:  Updated Attributes for: {guac_user_name}, "
                     f"Password: {guac_user_password}", debug)

        response = gconn.update_user_password('', guac_user_password,
                                              {"guac-organization": user_org})
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg(f"Guacamole:  Updated Password for: {guac_user_name}, "
                     f"Password: {guac_user_password}", debug)


def delete_user_accts(gconn: object,
                      users: list,
                      debug=False) -> None:
    """"Delete user accounts"""

    if not users:
        general_msg("Guacamole:  No Users Accounts to Delete")
        return

    general_msg("Guacamole:  Deleting User Accounts")
    for user in users:
        response = gconn.delete_user(user)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Deleted Account: "
                     f"{user}", debug)


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


def find_conn_group_id(conn_groups: dict,
                       org_name: str,
                       debug=False) -> str:
    """Locate connection group id"""

    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == org_name]
        return_id = group_id[0]
        info_msg(f"Guacamole:  Found {org_name}'s "
                 f"group ID(s): {group_id}", debug)

    except IndexError:
        general_msg(f"Guacamole:  {org_name} "
                    "has no connection group ID(s)")
        return_id = None
    return return_id


def find_child_groups(conn_list: list,
                      conn_group_id: str,
                      debug=False) -> dict:
    """Locate connection id"""

    conn_groups = {}
    try:
        for conn in conn_list.values():
            if conn.get('parentIdentifier') == conn_group_id:
                conn_groups[conn.get('name')] = conn.get('identifier')
        info_msg(f"Guacamole:  Found {conn_group_id}'s "
                 f"child groups: {conn_groups}", debug)
    except KeyError as error:
        error_msg(f"Guacamole ERROR:  {conn_group_id} "
                  f"has no child groups  {error}")
    return conn_groups


def find_conn_id(conn_list: list,
                 conn_name: str,
                 conn_group_id: str,
                 debug=False) -> str:
    """Locate connection id"""

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


def create_conn_groups(gconn: object,
                       create_groups: list,
                       conn_group_id: str,
                       org_name: str,
                       debug=False) -> dict:
    """Create connection group"""

    conn_groups = {}
    if conn_group_id:
        general_msg(f"Guacamole:  Orginization: {org_name} ""Already Exists")
        parent_id = conn_group_id
    else:
        general_msg(f"Guacamole:  Creating Orginization: {org_name}")
        conn_groups[org_name] = create_group(gconn,
                                             'ROOT',
                                             org_name,
                                             False,
                                             debug)
        parent_id = conn_groups[org_name]

    if create_groups:
        for group in create_groups:
            conn_groups[group] = create_group(gconn,
                                              parent_id,
                                              group,
                                              False,
                                              debug)
    else:
        general_msg("Guacamole:  No Connection Groups to Create")

    return conn_groups


def update_conn_groups(gconn: object,
                       group_vars: dict,
                       conn_group_id: str,
                       org_name: str,
                       debug=False) -> dict:
    """Create connection group"""

    delete_group_ids = group_vars['delete']
    create_groups = group_vars['create']
    update_groups = group_vars['update']

    delete_conn_groups(gconn,
                       delete_group_ids,
                       debug)

    conn_groups = {}
    if conn_group_id:
        general_msg(f"Guacamole:  Orginization: {org_name} ""Already Exists")
        parent_id = conn_group_id
    else:
        general_msg(f"Guacamole:  Creating Orginization: {org_name}")
        conn_groups[org_name] = create_group(gconn,
                                             'ROOT',
                                             org_name,
                                             True,
                                             debug)
        parent_id = conn_groups[org_name]

    if create_groups:
        for group in create_groups:
            conn_groups[group] = create_group(gconn,
                                              parent_id,
                                              group,
                                              False,
                                              debug)
    else:
        general_msg("Guacamole:  No Connection Groups to Create")

    if update_groups:
        general_msg("Guacamole:  Updating Connection Groups")
        for group in update_groups:
            conn_groups[group] = create_group(gconn,
                                              parent_id,
                                              group,
                                              True,
                                              debug)
    else:
        general_msg("Guacamole:  No Connection Groups to Update")

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
        response = gconn.delete_connection_group(group_id)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Deleted Group ID: "
                     f"{group_id}", debug)
        time.sleep(0.1)


def create_group(gconn: object,
                 parent: str,
                 child: str,
                 update=False,
                 debug=False) -> str:
    """Create connection group"""

    if update:
        group_id = get_conn_group_id(gconn, child, debug)
        time.sleep(0.1)
        response = gconn.update_connection_group(
            group_id,
            child,
            "ORGANIZATIONAL",
            parent,
            {
                'max-connections': '50',
                'max-connections-per-user': '10',
                'enable-session-affinity': ''
            }
        )
    else:
        response = gconn.create_connection_group(
            child,
            "ORGANIZATIONAL",
            parent,
            {
                'max-connections': '50',
                'max-connections-per-user': '10',
                'enable-session-affinity': ''
            }
        )
        time.sleep(0.1)
        group_id = get_conn_group_id(gconn, child, debug)

    message = parse_response(response)
    if message:
        info_msg(f"Guacamole:  {message}", debug)
    elif update:
        info_msg("Guacamole:  Updated Group: "
                 f"{child} under group ID: {parent}", debug)
    else:
        info_msg("Guacamole:  Created Group: "
                 f"{child} under group ID: {parent}", debug)

    time.sleep(0.1)
    return group_id


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
    if guacd_ips:
        general_msg("Guacamole:  Found Guacd servers. ")
        info_msg(f"Guacamole:  {guacd_ips}", debug)
    else:
        general_msg("Guacamole:  No Guacd servers found")

    for conn in create_conns:
        time.sleep(0.1)
        create_connection(gconn,
                          conn,
                          conn_groups,
                          guacd_ips,
                          conn_vars,
                          False,
                          debug)


def delete_user_conns(gconn: object,
                      delete_conn_ids: list,
                      debug=False) -> None:
    """Delete user connections"""

    if not delete_conn_ids:
        general_msg("Guacamole:  No User Connections to Delete")
        return

    general_msg("Guacamole:  Deleting User Connections")
    for conn_id in delete_conn_ids:
        response = gconn.delete_connection(conn_id)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}", debug)
        else:
            info_msg("Guacamole:  Deleted Connection ID: "
                     f"{conn_id}", debug)


def update_user_conns(gconn: object,
                      conn_params: dict,
                      conn_groups: dict,
                      guacd_ips: dict,
                      conn_vars: dict,
                      debug=False) -> None:
    """Updates user connections."""

    create_conns = conn_params['create']
    delete_conn_ids = conn_params['delete']
    update_conns = conn_params['update']

    delete_user_conns(gconn,
                      delete_conn_ids,
                      debug)

    create_user_conns(gconn,
                      create_conns,
                      conn_groups,
                      guacd_ips,
                      conn_vars,
                      debug)

    if not update_conns:
        general_msg("Guacamole:  No User Connections to Update")
        return

    general_msg("Guacamole:  Updating User Connections")
    for conn in update_conns:
        create_connection(gconn,
                          conn,
                          conn_groups,
                          guacd_ips,
                          conn_vars,
                          True,
                          debug)
        time.sleep(0.1)


def create_connection(gconn: object,
                      conn: dict,
                      conn_groups: dict,
                      guacd_ips: dict,
                      conn_vars: dict,
                      update=False,
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

    if update:
        req_type = "put"
        conn_id = get_conn_id(gconn,
                              conn_name,
                              conn_group_id,
                              debug)
    else:
        req_type = "post"
        conn_id = None
    response = gconn.manage_connection(
        req_type, conn_proto, conn_name,
        conn_group_id, conn_id,
        {
            "hostname": conn_ip,
            "port": "3389" if conn_proto == "rdp" else "22",
            "username": heat_user,
            "password": heat_pass,
            "domain": domain_name,
            "security": "any" if conn_proto == "rdp" else None,
            "ignore-cert": "true" if conn_proto == "rdp" else None
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
        info_msg(f"Guacamole:  Updated User Connection: {conn_name}.")
    else:
        info_msg(f"Guacamole:  Created User Connection: {conn_name}.")
    info_msg(f"Guacamole:  Username: {heat_user}, "
             f"Password: {heat_pass}, IP: {conn_ip}", debug)


def associate_user_conns(gconn: object,
                         conns: dict,
                         conn_groups: dict,
                         debug=False) -> None:
    """Associate user accounts with group_id and connections"""

    general_msg("Guacamole:  Associating User Connections")
    for conn in conns:
        conn_name = conn['name']
        conn_org = conn_name.split('.')[0]
        conn_group_id = conn_groups[conn_org]
        conn_id = get_conn_id(gconn, conn_name, conn_group_id, debug)
        time.sleep(0.1)

        response = gconn.update_user_connection(
            conn_name, conn_group_id, "add", True)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}")
        else:
            info_msg(f"Guacamole:  Associated {conn_name} "
                     f"to group: {conn_group_id}.", debug)
        time.sleep(0.1)

        response = gconn.update_user_connection(
            conn_name, conn_id, "add", False)
        message = parse_response(response)
        if message:
            info_msg(f"Guacamole:  {message}")
        else:
            info_msg(f"Guacamole:  Associated {conn_name} "
                     f"to connection: {conn_id}. ", debug)


def get_domain_name(heat_params: dict,
                    debug=False) -> str:
    """Retrieves the domain name from the given heat parameters."""

    try:
        domain_name = heat_params['domain_name']['default']
        info_msg(f"Guacamole:  Retrieved domain name: {domain_name}", debug)
        return domain_name
    except KeyError:
        info_msg("Guacamole:  Did not find a domain name", debug)
        return ''


def parse_response(response: object) -> str:
    """Parse the response from the Guacamole API"""

    try:
        message = response.json().get('message')
    except json.decoder.JSONDecodeError:
        return ''
    if not message:
        return ''
    return message
