import constants
import guacamole
import json
import openstack
from openstack.config import loader

cloud = constants.CLOUD

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


def guac_list_group():
    vconnection = {"name": guac_connection_group, "id": None}
    response = guac_session.list_connection_groups()
    data = json.loads(response)

    for key in data.keys():
        #Initialize connection group dictionary and pull identifier for specific connection group
        name = data[key]['name']
        if name == vconnection["name"] and not vconnection["id"]:
            vconnection["id"] = key
    print(vconnection)

def create_usernames():
    new_usernames = [f'{guac_user_prefix}{username+1}' for username in range(0, guac_user_total)]
    return new_usernames

def create_user_conn_dict():
    instances = get_ostack_instances()
    usernames = create_usernames()
    user_conn_data = {}
    for user in usernames:
        user_num = user[user.find('.')+1:]
        user_conn_data[user] = [instance for instance in instances if instance['name'].endswith(f'{ostack_instance_id}.{user_num}')]
    return user_conn_data

def get_ostack_instances():
    instances = [{'name': instance.name, 'address': instance.public_v4} for instance in conn.list_servers()]
    return instances

def get_existing_accounts():
    existing_accounts = list(json.loads(guac_session.list_users()))
    return existing_accounts

def guac_manage_user_acct(guac_action, new_user_accounts):
    for username in new_user_accounts:
        if guac_action == "create":
            print(username)
            guac_session.create_user(f'{username}', guac_user_password, {"guac-organization": guac_user_organization})
            print(f"Created User: {username} with password {guac_user_password}")
        if guac_action == "delete":
            guac_session.delete_user(username)
            print(f'Deleted User: {username}')

def guac_manage_user_conns(guac_action, guac_user_conn_proto):
    vconnection = {"name": guac_connection_group, "id": None}
    conn_groups = json.loads(guac_session.list_connection_groups())
    user_conn_data = create_user_conn_dict()
    usernames=create_usernames()

    for key in conn_groups.keys():
        name = conn_groups[key]['name']
        if name == vconnection['name'] and not vconnection['id']:
            vconnection['id'] = key

    for user, server_list in user_conn_data.items():
        for server in server_list:
            instance_name = server.get('name')
            instance_address = server.get('address')
            if guac_action == "create":
                for proto in guac_user_conn_proto:
                    if proto == "ssh":
                        guac_session.manage_connection("post", "ssh", f'{guac_event_prefix}.{user}.{instance_name}.ssh', vconnection["id"], None, {"hostname": instance_address, "port": "22", "username": ostack_instance_username, "password": ostack_instance_pw}, {"max-connections": "", "max-connections-per-user": "1" })
                    if proto == "rdp":
                        guac_session.manage_connection("post", "rdp", f'{guac_event_prefix}.{user}.{instance_name}.rdp', vconnection["id"], None, {"hostname": instance_address, "port": "3389", "username": ostack_instance_username, "password": ostack_instance_pw, "security": "any", "ignore-cert": "true"}, {"max-connections": "", "max-connections-per-user": "1" })

    print(guac_session.list_connections())
            # if guac_action == "delete":
            #     for proto in guac_user_conn_



def main():
    guac_manage_user_conns(guac_action, guac_user_conn_proto)







    # if guac_action == "create":





    # elif guac_action == "delete":




    # else:
    #     print("No Action Defined")


if __name__ == '__main__':
    main()