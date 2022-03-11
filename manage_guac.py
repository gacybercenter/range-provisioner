import constants
import guacamole
import json
import openstack
import yaml
from openstack.config import loader

cloud = "gcr"

guac_action = constants.GUAC_ACTION
guac_user_total = constants.GUAC_USER_TOTAL
guac_user_prefix = constants.GUAC_USER_PREFIX
guac_user_password = constants.GUAC_USER_PASSWORD
guac_user_conn_proto = constants.GUAC_USER_CONN_PROTO
guac_user_organization = constants.GUAC_USER_ORGANIZATION
guac_connection_group = constants.GUAC_CONN_GROUP
guac_host = constants.GUAC_HOST
guac_datasource = constants.GUAC_DATASOURCE
guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS
guac_event_prefix = constants.GUAC_EVENT_PREFIX

ostack_instance_id = constants.OSTACK_INSTANCE_ID
ostack_instance_username = constants.OSTACK_INSTANCE_USERNAME
ostack_instance_pw = constants.OSTACK_INSTANCE_PW


config = loader.OpenStackConfig()
conn = openstack.connect(cloud=cloud)
guac_session = guacamole.session(guac_host, guac_datasource, guac_admin, guac_password)


def create_usernames():
    new_usernames = [f'{guac_user_prefix}{username+1}' for username in range(guac_user_total)]
    return new_usernames

def create_instance_dict():
    instances = get_ostack_instances()
    usernames = create_usernames()
    instance_dict = {}
    for user in usernames:
        user_num = user[user.find('.')+1:]
        instance_dict[user] = [instance for instance in instances if instance['name'].endswith(f'{ostack_instance_id}.{user_num}')]
    return instance_dict

def get_ostack_instances():
    instances = [{'name': instance.name, 'address': instance.public_v4} for instance in conn.list_servers()]
    return instances

def get_existing_accounts():
    existing_accounts = list(json.loads(guac_session.list_users()))
    return existing_accounts

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
    conn_groups = json.loads(guac_session.list_connection_groups())
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
            vuser_conns = json.loads(guac_session.list_connections())
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
    guac_manage_user_acct(guac_action)
    guac_manage_user_conns(guac_action, guac_user_conn_proto)

    
if __name__ == '__main__':
    main()