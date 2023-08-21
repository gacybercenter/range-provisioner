import json
import time
import orchestration.heat as heat
from utils.generate import generate_instance_names, create_user_list
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              users_list,
              instances_list,
              debug=False):
    """Provision container and upload assets"""

    # Check if connection group exists
    connection_group_name = guacamole_globals['conn_group_name']

    if get_conn_group_id(gconn, connection_group_name):
        conn_group_id = (get_conn_group_id(gconn, connection_group_name))[0]
        general_msg(
            f"Retrieved {connection_group_name}'s connection ID: {conn_group_id}")
    else:
        conn_group_id = None
        error_msg(f"Could not find {connection_group_name}'s connection ID")
    
    info_msg(users_list, debug)

    instances = get_ostack_instances(conn)
    general_msg("Retrieved OS Stack Instances:")
    info_msg(instances, debug)

    # Create user accounts
    for guac_user in users_list:

        user_num = f"{guac_user}".rsplit('.', 1)[1]

        if guacamole_globals['provision']:

            guac_password = users_list[guac_user]['password']
            general_msg(f"Creating user account: {guac_user}")
            general_msg(f"Password: {guac_password}")

            if guac_user in get_existing_accounts(gconn):
                error_msg("Guacamole ERROR:  Can't create user account, "
                          f"{guac_user} already exists")
            else:
                general_msg(
                    f"create_user_acct: {gconn}, {guac_user}, {guac_password}, {guacamole_globals['user_org']}")
                # create_user_acct(
                #     gconn,
                #     guac_user,
                #     guac_password,
                #     guacamole_globals['user_org'])
                # Create instance connections

                # for instance in instances_list:
                # general_msg(f"{guacamole_globals['conn_group_name']}.{user_num}")

                # create_user_conns(
                #     gconn,
                #     guacamole_globals['action'],
                #     guac_user,
                #     instances,
                #     heat_params['conn_proto']['default'],
                #     conn_group_id,
                #     heat_params['username']['default'],
                #     heat_params['password']['default'])
        # Delete user accounts as specified in globals template
        else:
            if guac_user not in get_existing_accounts(gconn):
                error_msg("Guacamole ERROR:  Can't delete user account,"
                          f" {guac_user} doesn't exist")
            else:
                general_msg(f"delete_user_acct: {gconn}, {guac_user}")

                # delete_user_acct(gconn, guac_user)

                # Delete instance connections
                instances = [
                    {
                        'name': instance.name,
                        'address': instance.public_v4
                    }
                    for instance in instances_list
                    if instance['name'].endswith(
                        f"{guacamole_globals['conn_name']}.{user_num}")]

                general_msg(
                    f"create_user_conns: {gconn}, {guacamole_globals['action']}, {guac_user}, {instances}, {heat_params['conn_proto']['default']}, {conn_group_id}, {heat_params['username']['default']}, {heat_params['password']['default']}")

                # create_user_conns(
                #     gconn,
                #     guacamole_globals['action'],
                #     guac_user,
                #     instances,
                #     heat_params['conn_proto']['default'],
                #     conn_group_id,
                #     heat_params['username']['default'],
                #     heat_params['password']['default'])
            # Delete connection groups if specified in globals template
            if conn_group_id is None:
                error_msg(f"Guacamole ERROR:  Can't delete connection group,"
                          f" {connection_group_name} doesn't exist")
            else:
                general_msg(
                    f"delete_conn_group: {gconn}, {connection_group_name}, {conn_group_id}")
                # delete_conn_group(gconn,
                #                   connection_group_name,
                #                   conn_group_id)
    success_msg("Provisioned Guacamole")
    return


def deprovision(conn, globals, guacamole_globals, sec_params, debug=False):
    return


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.


def get_ostack_instances(conn):
    """Obtain openstack instance names and public addresses"""
    instances = [
        {
            'name': instance.name,
            'address': instance.public_v4
        }
        for instance in conn.list_servers()
    ]
    return instances


def get_existing_accounts(gconn):
    """Locate existing user accounts"""
    existing_accounts = list(json.loads(gconn.list_users()))
    return existing_accounts


def get_conn_group_id(gconn, conn_group_name):
    """Locate connection group id"""
    conn_groups = json.loads(gconn.list_connection_groups())
    try:
        group_id = [key for key in conn_groups.keys()
                    if conn_groups[key]['name'] == conn_group_name]
    except Exception as e:
        error_msg(f"Guacamole ERROR:  {conn_group_name}"
                  f" is missing from group list \n {e}")
    info_msg(group_id)
    return group_id


def get_conn_id(gconn, conn_name, conn_group_id):
    """Locate connection id"""
    list_conns = json.loads(gconn.list_connections())
    try:
        conn_id = ([k for k, v in list_conns.items()
                   if v.get('parentIdentifier') == conn_group_id
                   and v.get('name') == conn_name])
    except Exception as e:
        error_msg(f"Guacamole ERROR:  {conn_name}"
                  f" is missing from connection list \n {e}")
    return conn_id


def create_conn_group(gconn, conn_group_name):
    """Create connection group"""
    gconn.create_connection_group(
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
    success_msg(f"Guacamole:  The connection group {conn_group_name} was created")


def delete_conn_group(gconn, conn_group_name, conn_group_id):
    """Delete connection group"""
    gconn.delete_connection_group(conn_group_id)
    success_msg(f"Guacamole:  The connection group {conn_group_name}"
                f" with id {conn_group_id} was deleted")


def create_user_acct(gconn, user, guac_user_password, guac_user_organization):
    """"Create user accounts"""
    gconn.create_user(f'{user}', guac_user_password,
                      {"guac-organization": guac_user_organization})
    success_msg(f"Guacamole:  Created User Account: {user}")


def delete_user_acct(gconn, user):
    """"Delete user accounts"""
    gconn.delete_user(user)
    success_msg(f'Guacamole:  Deleted User Account: {user}')


def create_user_conns(gconn, conn_action, user, instances, conn_proto,
                      conn_group_id, ostack_username, ostack_pass):
    """Create/Delete user connections"""
    for instance in instances:
        if instance['address']:
            if "ssh" in conn_proto:
                conn_name = f"{instance['name']}.ssh"
                if conn_action == "delete":
                    delete_user_conns(gconn, user, conn_name, conn_group_id)
                else:
                    gconn.manage_connection(
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
                    success_msg(f"Guacamole:  Created connection for {instance['name']}"
                                f" ssh connection with address: {instance['address']}")
                    associate_user_conns(gconn, user, conn_name, conn_group_id)
            if "rdp" in conn_proto:
                conn_name = f"{instance['name']}.rdp"
                if conn_action == "delete":
                    delete_user_conns(gconn, user, conn_name, conn_group_id)
                else:
                    gconn.manage_connection(
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
                    success_msg(f"Guacamole:  Created connection for {instance['name']}"
                                f" rdp connection with address: {instance['address']}")
                    associate_user_conns(gconn, user, conn_name, conn_group_id)


def associate_user_conns(gconn, user, conn_name, conn_group_id):
    """Associate user accounts with group_id and connections"""
    time.sleep(2)
    conn = get_conn_id(gconn, conn_name, conn_group_id)[0]
    gconn.update_user_connection(user, conn_group_id, "add", True)
    gconn.update_user_connection(user, conn, "add", False)
    print(f"Guacamole:  Associated {conn_name} connection for {user}")


def delete_user_conns(gconn, user, conn_name, conn_group_id):
    """Delete user connections"""
    conn_id = get_conn_id(gconn, conn_name, conn_group_id)[0]
    gconn.delete_connection(conn_id)
    print(f"Guacamole:  Deleted associated {conn_name}"
          f" connection for {user}")
