import constants
import guacamole
from json import loads
from yaml import safe_load
from openstack import config, connect, enable_logging

guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS


guac_user_prefix = constants.GUAC_USER_PREFIX
guac_user_organization = constants.GUAC_USER_ORGANIZATION
guac_connection_group = constants.GUAC_CONN_GROUP

guac_event_prefix = constants.GUAC_EVENT_PREFIX

ostack_instance_id = constants.OSTACK_INSTANCE_ID
ostack_instance_username = constants.OSTACK_INSTANCE_USERNAME
ostack_instance_pw = constants.OSTACK_INSTANCE_PW


def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


def create_usernames(num_users, username):
    new_usernames = [f'{username}.{num}' for num in range(1, num_users+1)]
    return new_usernames


def create_instance_dict(instances, usernames):
    instance_dict = {}
    for user in usernames:
        user_num = user[user.find('.')+1:]
        instance_dict[user] = [instance for instance in instances if instance['name'].endswith(f'{ostack_instance_id}.{user_num}')]
    return instance_dict


def get_ostack_instances():
    instances = [{'name': instance.name, 'address': instance.public_v4} for instance in conn.list_servers()]
    return instances


def get_existing_accounts():
    existing_accounts = list(loads(guac_session.list_users()))
    return existing_accounts


def get_conn_group_id(conn_group_name):
    conn_groups = list_conn_groups()
    group_id = [ key for key in conn_groups.keys() if conn_groups[key]['name'] == conn_group_name and not None ]
    return group_id


def list_conn_groups():
    conn_groups = loads(guac_session.list_connection_groups())
    return conn_groups


def create_conn_group(conn_group_name):
    guac_session.create_connection_group(f'{conn_group_name}',
                                         "ORGANIZATIONAL",
                                         "ROOT",
                                         {'max-connections': '50',
                                         'max-connections-per-user' : '10',
                                         'enable-session-affinity' : ''})
    print(f"Guacamole:  The connection group {conn_group_name} was created")


def delete_conn_group(conn_group_name, conn_group_id):
    guac_session.delete_connection_group(conn_group_id)
    print(f"Guacamole:  The connection group {conn_group_name} with id {conn_group_id} was deleted")


def guac_manage_user_acct(guac_action):
    usernames=create_usernames()

    for username in usernames:
        if guac_action == "create":
            guac_session.create_user(f'{username}', guac_user_password, {"guac-organization": guac_user_organization})
            print(f"Guacamole:  Created User Account: {username}")
        if guac_action == "delete":
            guac_session.delete_user(username)
            print(f'Guacamole:  Deleted User Account: {username}')


def guac_manage_user_conns(guac_action, guac_user_conn_proto):
    vconnection = {'name': guac_connection_group}
    conn_groups = loads(guac_session.list_connection_groups())
    instance_dict = create_instance_dict()

    group_id = [ key for key in conn_groups.keys() if conn_groups[key]['name'] == guac_connection_group and not None ]
    if group_id:
        vconnection.update({'group_id': group_id[0]})

    for user, server_list in instance_dict.items():
        for server in server_list:
            server_name = server.get('name')
            vconnection.update({'instance_name': server_name})
            vconnection.update({'guac_instance_name': f'{guac_event_prefix}.{user}.{server_name}'})
            vconnection.update({'user': user})
            vconnection.update({'instance_address': server.get('address')})

            if guac_action == "create":
                for proto in guac_user_conn_proto:
                    if proto == "ssh":
                        guac_session.manage_connection("post", "ssh", vconnection['guac_instance_name'] + ".ssh", vconnection['group_id'], None, {"hostname": vconnection['instance_address'], "port": "22", "username": ostack_instance_username, "password": ostack_instance_pw}, {"max-connections": "", "max-connections-per-user": "1" })
                        print(f'Guacamole:  Created connection for {vconnection["guac_instance_name"]} ssh connection with address: {vconnection["instance_address"]}')
                    if proto == "rdp":
                        guac_session.manage_connection("post", "rdp", vconnection['guac_instance_name'] + ".rdp", vconnection['group_id'], None, {"hostname": vconnection['instance_address'], "port": "3389", "username": ostack_instance_username, "password": ostack_instance_pw, "security": "any", "ignore-cert": "true"}, {"max-connections": "", "max-connections-per-user": "1" })
                        print(f'Guacamole:  Created connection for {vconnection["guac_instance_name"]} rdp connection with address: {vconnection["instance_address"]}')
            vuser_conns = loads(guac_session.list_connections())
            vuser_conn_id = [ key for key in vuser_conns.keys() if vuser_conns[key]['name'].startswith(vconnection['guac_instance_name']) ]
            if vuser_conn_id and guac_action == "create":
                vconnection.update({'conn_id': vuser_conn_id[0]})
                guac_session.update_user_connection(vconnection['user'], vconnection['group_id'], "add", True)
                guac_session.update_user_connection(vconnection['user'], vconnection['conn_id'], "add", False)
                print(f'Guacamole:  Associated connections for {vconnection["user"]} with id {vconnection["conn_id"]} for server {vconnection["guac_instance_name"]}')
            
            if guac_action == "delete":
                vconnection.update({'conn_id': vuser_conn_id[0]})
                if vconnection['user']:
                    guac_session.delete_connection(vconnection['conn_id'])
                    print(f'Guacamole:  Deleted connection for {vconnection["guac_instance_name"]} with {vconnection["conn_id"]}')


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
    
    usernames = create_usernames(guac_dict['num_users'], guac_dict['username'])
    conn_group_id = get_conn_group_id(guac_dict['conn_group_name'])


# Create/Delete connection groups if specified in globals template
    if guac_dict['conn_group_action'] == "create":
        if conn_group_id:
            print(f"Guacamole ERROR:  Can't create connection group, {guac_dict['conn_group_name']} already exists")
        else:
            create_conn_group(guac_dict['conn_group_name'])
    if guac_dict['conn_group_action'] == "delete":
            if not conn_group_id:
                print(f"Guacamole ERROR:  Can't delete connection group, {guac_dict['conn_group_name']} doesn't exist")
            else:
                delete_conn_group(guac_dict['conn_group_name'], conn_group_id[0])
    
    
    # print(loads(guac_session.list_connection_groups()))



    # guac_session.create_connection_group('test_group', "ORGANIZATIONAL", "ROOT", {'max-connections': '50', 'max-connections-per-user' : '10', 'enable-session-affinity' : ''})
    # guac_session.delete_connection_group(16)


    # print(get_ostack_instances())


    # guac_manage_user_conns(guac_action, guac_user_conn_proto)

    
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
