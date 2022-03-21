import constants
import guacamole
from json import loads
from yaml import safe_load
from openstack import config, connect, enable_logging
import time

guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS
guac_user_password = constants.GUAC_USER_PASSWORD


def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


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


def main():
    # Load templates
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)

    # Create dictionaries
    global_dict = ([v for k, v in global_params.items() if k == "global"])[0]
    guac_dict = ([v for k, v in global_params.items() if k == "guacamole"])[0]
    heat_dict = ([v for k, v in heat_params.items() if k == "parameters"])[0]
    guac_dict.update({'conn_name':
                     f"{heat_dict['instance_id']['default']}"
                     f".{global_dict['username_prefix']}"})
    
    # Check global for create_all value
    if global_dict['create_all'] is True:
        guac_dict.update(
            {
                'action': 'create',
                'conn_group_action': 'create',
            }
            )
    if global_dict['create_all'] is False:
                guac_dict.update(
            {
                'action': 'delete',
                'conn_group_action': 'delete',
            }
            )
    else:
        pass

    instance_list = conn.list_servers()

    # Check if connection group exists
    if get_conn_group_id(guac_dict['conn_group_name']):
        conn_group_id = (get_conn_group_id(guac_dict['conn_group_name']))[0]
    else:
        conn_group_id = None

    # Create connection groups as specified in globals template
    if guac_dict['conn_group_action'] == "create":
        if conn_group_id:
            print("Guacamole ERROR:  Can't create connection group,"
                  f" {guac_dict['conn_group_name']} already exists")
        else:
            create_conn_group(guac_dict['conn_group_name'])
            time.sleep(3)
            conn_group_id = (get_conn_group_id(
                guac_dict['conn_group_name']))[0]

    # Create user accounts as specified in globals template
    usernames = create_usernames(global_dict['num_users'], global_dict['username_prefix'])
    for user in usernames:
        user_num = f"{user}".rsplit('.', 1)[1]
        if guac_dict['action'] == 'create':

            if user in get_existing_accounts():
                print("Guacamole ERROR:  Can't create user account,"
                      f"{user} already exists")
            else:
                create_user_acct(
                    user,
                    guac_user_password,
                    guac_dict['user_org']
                    )
                # Create instance connections
                instances = [
                    {
                        'name': instance.name,
                        'address': instance.public_v4
                    }
                    for instance in instance_list
                    if instance['name'].endswith(
                        f"{guac_dict['conn_name']}.{user_num}"
                        )
                            ]

                create_user_conns(
                    guac_dict['action'],
                    user, instances, heat_dict['conn_proto']['default'],
                    conn_group_id, heat_dict['username']['default'],
                    heat_dict['password']['default']
                    )

        # Delete user accounts as specified in globals template
        if guac_dict['action'] == 'delete':
            if user not in get_existing_accounts():
                print("Guacamole ERROR:  Can't delete user account,"
                      f" {user} doesn't exist")
            else:
                delete_user_acct(user)
                # Delete instance connections
                instances = [
                    {
                        'name': instance.name,
                        'address': instance.public_v4
                    }
                    for instance in instance_list
                    if instance['name'].endswith(
                        f"{guac_dict['conn_name']}.{user_num}"
                        )
                            ]
                create_user_conns(
                    guac_dict['action'],
                    user,
                    instances,
                    heat_dict['conn_proto']['default'],
                    conn_group_id, heat_dict['username']['default'],
                    heat_dict['password']['default']
                    )

    # Delete connection groups if specified in globals template
    if guac_dict['conn_group_action'] == "delete":
        if conn_group_id is None:
            print(f"Guacamole ERROR:  Can't delete connection group,"
                  f" {guac_dict['conn_group_name']} doesn't exist")
        else:
            delete_conn_group(guac_dict['conn_group_name'], conn_group_id)


if __name__ == '__main__':
    print("***  Begin Guacamole script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template(globals_template)['heat']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    config = config.loader.OpenStackConfig()
    conn = connect(cloud=load_template(
        globals_template)['global']['cloud'])
    enable_logging(debug=load_template(
        globals_template)['global']['debug'])
    guac_host = load_template(globals_template)['guacamole']['guac_host']
    guac_session = guacamole.session(
                                    guac_host,
                                    "mysql",
                                    guac_admin,
                                    guac_password
                                    )
    main()
    print("\n*** End Guacamole script  ***")
