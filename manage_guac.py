import constants
import guacamole
from json import loads
from yaml import safe_load
from openstack import config, connect, enable_logging
import time

guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS

def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


def create_usernames(num_users, username):
    """Create username list"""
    new_usernames = [f'{username}.{num}' for num in range(1, num_users+1)]
    return new_usernames


def create_instance_dict(instances, usernames):
    """Create instance dictionary"""
    instance_dict = {}
    for user in usernames:
        user_num = user[user.find('.')+1:]
        instance_dict[user] = [instance for instance in instances if instance['name'].endswith(f'{ostack_instance_id}.{user_num}')]
    return instance_dict


def get_ostack_instances():
    """Obtain openstack instance names and public addresses"""
    instances = [{'name': instance.name, 'address': instance.public_v4} for instance in conn.list_servers()]
    return instances


def get_existing_accounts():
    """Locate existing user accounts"""
    existing_accounts = list(loads(guac_session.list_users()))
    return existing_accounts


def get_conn_group_id(conn_group_name):
    """Locate connection group id"""
    conn_groups = loads(guac_session.list_connection_groups())
    try:
        group_id = [ key for key in conn_groups.keys() if conn_groups[key]['name'] == conn_group_name and not None ]
    except Exception as e:
        print(f"Guacamole ERROR:  {conn_group_name} is missing from group list \n {e}")
    return group_id


def get_conn_id(conn_name, conn_group_id):
    """Locate connection id"""
    list_conns = loads(guac_session.list_connections())
    try:
        conn_id = ([ k for k,v in list_conns.items() if v.get('parentIdentifier') == conn_group_id and v.get('name') == conn_name ])[0]
    except Exception as e:
        print(f"Guacamole ERROR:  {conn_name} is missing from connection list \n {e}")
    return conn_id


def create_conn_group(conn_group_name):
    """Create connection group"""
    guac_session.create_connection_group(f'{conn_group_name}',
                                         "ORGANIZATIONAL",
                                         "ROOT",
                                         {'max-connections': '50',
                                         'max-connections-per-user' : '10',
                                         'enable-session-affinity' : ''})
    time.sleep(3)
    print(f"Guacamole:  The connection group {conn_group_name} was created")


def delete_conn_group(conn_group_name, conn_group_id):
    """Delete connection group"""
    guac_session.delete_connection_group(conn_group_id)
    print(f"Guacamole:  The connection group {conn_group_name} with id {conn_group_id} was deleted")


def create_user_acct(user, guac_user_password, guac_user_organization):
    """"Create user accounts"""
    guac_session.create_user(f'{user}', guac_user_password, {"guac-organization": guac_user_organization})
    print(f"Guacamole:  Created User Account: {user}")


def delete_user_acct(user):
    """"Delete user accounts"""
    guac_session.delete_user(user)
    print(f'Guacamole:  Deleted User Account: {user}')


def create_user_conns(conn_action, user, instances, conn_proto, conn_group_id, ostack_username, ostack_pass):
    """Create/Delete user connections"""
    for instance in instances:
        conn_name_ssh = f"{instance['name']}.ssh"
        conn_name_rdp = f"{instance['name']}.rdp"
        if conn_action == "delete":
            conn_names = [ conn_name_ssh, conn_name_rdp ]
            delete_user_conns(user, conn_names, conn_group_id)
        else:
            if "ssh" in conn_proto:
                guac_session.manage_connection("post", "ssh", conn_name_ssh, conn_group_id, None, {"hostname": instance['address'], "port": "22", "username": ostack_username, "password": ostack_pass}, {"max-connections": "", "max-connections-per-user": "2" })
                print(f"Guacamole:  Created connection for {instance['name']} ssh connection with address: {instance['address']}")
                associate_user_conns(user, conn_name_ssh, conn_group_id)
            if "rdp" in conn_proto:
                guac_session.manage_connection("post", "rdp", conn_name_rdp, conn_group_id, None, {"hostname": instance['address'], "port": "3389", "username": ostack_username, "password": ostack_pass, "security": "any", "ignore-cert": "true"}, {"max-connections": "", "max-connections-per-user": "2" })
                print(f"Guacamole:  Created connection for {instance['name']} rdp connection with address: {instance['address']}")
                associate_user_conns(user, conn_name_rdp, conn_group_id)

def associate_user_conns(user, conn_name, conn_group_id):
    """Associate user accounts with group_id and connections"""
    time.sleep(3)
    conn = get_conn_id(conn_name, conn_group_id)
    guac_session.update_user_connection(user, conn_group_id, "add", True)
    guac_session.update_user_connection(user, conn, "add", False)
    print(f"Guacamole:  Associated {conn_name} connection for {user}")

def delete_user_conns(user, conn_names, conn_group_id):
    """Delete user connections"""
    for connection in conn_names:
        conn_id = get_conn_id(connection, conn_group_id)
        guac_session.delete_connection(conn_id)
        print(f"Guacamole:  Deleted associated {connection} connection for {user}")


def main():
    # Create main dictionary and load templates
    guac_dict = {}
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)

    # Update main dictionary and update keys and values loaded from templates
    guac_dict.update({'num_users':
                     global_params['global']['num_users']})
    guac_dict.update({'guac_action':
                     global_params['guacamole']['action']})
    guac_dict.update({'username':
                     global_params['guacamole']['username_prefix']})
    guac_dict.update({'user_org':
                     global_params['guacamole']['user_org']})
    guac_dict.update({'conn_group_action':
                     global_params['guacamole']['conn_group_action']})
    guac_dict.update({'conn_group_name':
                     global_params['guacamole']['conn_group_name']})
    guac_dict.update({'conn_proto':
                     heat_params['parameters']['guac_conns']['default']})
    guac_dict.update({'conn_name':
                     heat_params['parameters']['name']['default']})
    guac_dict.update({'ostack_instance_username':
                     heat_params['parameters']['username']['default']})
    guac_dict.update({'ostack_instance_password':
                     heat_params['parameters']['password']['default']})
    
    instance_list = conn.list_servers()

    # Check if connection group exists
    if get_conn_group_id(guac_dict['conn_group_name']):
        conn_group_id = (get_conn_group_id(guac_dict['conn_group_name']))[0]
    else:
        conn_group_id = None

    # Create connection groups as specified in globals template
    if guac_dict['conn_group_action'] == "create":
        if conn_group_id:
            print(f"Guacamole ERROR:  Can't create connection group, {guac_dict['conn_group_name']} already exists")
        else:
            create_conn_group(guac_dict['conn_group_name'])
            conn_group_id = (get_conn_group_id(guac_dict['conn_group_name']))[0]

    # Create user accounts as specified in globals template
    usernames = create_usernames(guac_dict['num_users'], guac_dict['username'])
    for user in usernames:
        if guac_dict['guac_action'] == 'create':
            if user in get_existing_accounts():
                print(f"Guacamole ERROR:  Can't create user account, {user} already exists")
            else:
                create_user_acct(user, guac_user_password, guac_dict['user_org'])
                # Create instance connections
                user_num = f"{user}".rsplit('.', 1)[1]
                instances = [ {'name': instance.name, 'address': instance.public_v4} for instance in instance_list if instance['name'].endswith(f"{guac_dict['conn_name']}.{user_num}") ]
                create_user_conns(guac_dict['guac_action'], user, instances, guac_dict['conn_proto'], conn_group_id, guac_dict['ostack_instance_username'], guac_dict['ostack_instance_password'])

        # Delete user accounts as specified in globals template
        if guac_dict['guac_action'] == 'delete':
            if user not in get_existing_accounts():
                print(f"Guacamole ERROR:  Can't delete user account, {user} doesn't exist")
            else:
                delete_user_acct(user)
                # Delete instance connections
                user_num = f"{user}".rsplit('.', 1)[1]
                instances = [ {'name': instance.name, 'address': instance.public_v4} for instance in instance_list if instance['name'].endswith(f"{guac_dict['conn_name']}.{user_num}") ]
                create_user_conns(guac_dict['guac_action'], user, instances, guac_dict['conn_proto'], conn_group_id, guac_dict['ostack_instance_username'], guac_dict['ostack_instance_password'])

    # Delete connection groups if specified in globals template
    if guac_dict['conn_group_action'] == "delete":
            if conn_group_id is None:
                print(f"Guacamole ERROR:  Can't delete connection group, {guac_dict['conn_group_name']} doesn't exist")
            else:
                delete_conn_group(guac_dict['conn_group_name'], conn_group_id)

    
if __name__ == '__main__':
    print("***  Begin Guacamole script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template(globals_template)['openstack']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    config = config.loader.OpenStackConfig()
    conn = connect(cloud=load_template
                    (globals_template)['global']['cloud'])
    enable_logging(debug=load_template
                   (globals_template)['global']['debug'])
    guac_host = load_template(globals_template)['guacamole']['guac_host']
    guac_session = guacamole.session(guac_host, "mysql", guac_admin, guac_password)
    main()
    print("\n*** End Guacamole script  ***")
