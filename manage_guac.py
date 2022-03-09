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
guac_user_connection = constants.GUAC_USER_CONNECTION
guac_user_organization = constants.GUAC_USER_ORGANIZATION
guac_connection_group = constants.GUAC_CONN_GROUP
guac_host = constants.GUAC_HOST
guac_datasource = constants.GUAC_DATASOURCE
guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS
ostack_instance_id = constants.OSTACK_INSTANCE_ID
# stack_id = constants.STACK_ID

config = loader.OpenStackConfig()
conn = openstack.connect(cloud=cloud)
guac_session = guacamole.session(guac_host, guac_datasource, guac_admin, guac_password)
user_accounts = []
new_user_accounts = []


def get_instances():
    return [{'name': instance.name, 'address': instance.public_v4} for instance in conn.list_servers()]

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

def get_guac_user_accounts():
    response = guac_session.list_users()
    data = json.loads(response)

    for account_name in data.keys():
        if account_name.startswith(guac_user_prefix):
            user_accounts.append(account_name)
    return user_accounts

def guac_manage_user_acct(guac_action, new_user_accounts):
    for username in new_user_accounts:
        if guac_action == "create":
            print(username)
            guac_session.create_user(f'{username}', guac_user_password, {"guac-organization": guac_user_organization})
            print(f"Created User: {username} with password {guac_user_password}")
        if guac_action == "delete":
            guac_session.delete_user(username)
            print(f'Deleted User: {username}')

def guac_manage_user_conns(new_user_accounts, instances):
    vconnection = {"name": guac_connection_group, "id": None}
    response = guac_session.list_connection_groups()
    data = json.loads(response)

    for key in data.keys():
        name = data[key]['name']
        if name == vconnection['name'] and not vconnection['id']:
            vconnection['id'] = key

    users = {}

    for user in new_user_accounts:
        user_num = user[user.find('.')+1:]
        users[user] = [instance for instance in instances if instance['name'].endswith(user_num)]

    for user,server_list in users.items():
        for item in server_list:
            print(user,item.get('name'),item.get('address'))



        # instance_name = instance_value['name']

        # for instance_key, instance_value in instances.items():
        #     for num in range(0, guac_user_total):
        #         if instance_key.endswith(f'{ostack_instance_id}.{num}'):
        #             instance_name = instance_value['name']
        #             public_ip = instance_value['address']
        #             print(instance_name, public_ip)

    # guac_session.manage_connection("post", "ssh", )




    # for num in range(0, guac_user_total):
    #     for username in new_user_accounts:
            # if instances.name.endswith(f'{ostack_instance_id}.{num}'):
            #     print(instances.name)
        # if conn_type == "ssh":
        #     connection = guac_session.manage_connection("post", "ssh", username, vconnection["id"], None, {"hostname": instances})

    
    # for username in new_user_accounts:
    #     if conn_type == "ssh":
    #         print()
        # if conn_type == "rdp":





    # print(vuser_connections)


def main():
    # Create new user account list
    for username in range(0, guac_user_total):
        username = f'{guac_user_prefix}{username+1}'
        new_user_accounts.append(username)
    
    # print(get_instances())
    
    instances = get_instances()
    guac_manage_user_conns(new_user_accounts, instances)

    # print(get_guac_user_accounts())

    # print(conn._list_servers())
    # guac_manage_user_acct(guac_action, new_user_accounts)






    # if guac_action == "create":





    # elif guac_action == "delete":




    # else:
    #     print("No Action Defined")


if __name__ == '__main__':
    main()