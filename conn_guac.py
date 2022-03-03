import constants
import guacamole
import json
import openstack
from openstack.config import loader

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
stack_id = constants.STACK_ID

instances = {}

def guac_session(guac_host, guac_datasource, guac_admin, guac_password):
    guac_session = guacamole.session(guac_host, guac_datasource, guac_admin, guac_password)
    guac_session.generate_token()


def get_instances():
    config = loader.OpenStackConfig()
    conn = openstack.connect()
    for server in conn.compute.servers():
        if server.name.startswith(f'{guac_user_prefix}'):
            id = server.name.split(".")[2]
            instances[id] = {"name": server.name, 'address': server.addresses['public'][0]['addr']}
    return instances

def guac_create_user():
    # # NOTE: Initializing connection group dictionary and pulling identifier for specific connection group
    vconnection = {"name": guac_connection_group, "id": None}
    response = guac_session.list_connection_groups()
    data = json.loads(response)

    for key in data.keys():
        name = data[key]['name']
        if name == vconnection["name"] and not vconnection["id"]:
            vconnection["id"] = key
            # print(vconnection)
    for user in range(0, guac_user_total):
        user = str(user)
        guac_session.create_user(guac_user_prefix + user, guac_user_password, {"guac-organization": guac_user_organization})
        print(f"Created User: {guac_user_prefix}{user} with password {guac_user_password}")
        guac_session.update_user_connection(guac_user_prefix + user, vconnection["id"], "add", True)
        print(f"Associated Connectiongroup for {vconnection['name']} to {guac_user_prefix}{user}")
    

def guac_create_conn():
        if guac_user_connection == "ssh":
            connection = guac_session.manage_connection("post", "ssh", guac_user_prefix + user, vconnection["id"], None, {"hostname": instances[user]["address"], "port": "22", "username": "user", "password": guac_user_password}, {"max-connections": "", "max-connections-per-user": "1" })
        if guac_user_connection == "rdp":
            connection = guac_session.manage_connection("post", "rdp", guac_user_prefix + user, vconnection["id"], None, {"hostname": instances[user]["address"], "port": "3389", "username": "user", "password": guac_user_password, "security": "any", "ignore-cert": "true"}, {"max-connections": "", "max-connections-per-user": "1" })
        print(f'Created Connection for: {instances[user]["address"]}')
    
        vuser_connections = []
        response = guac_session.list_connections()
        data = json.loads(response)

        for key in data.keys():
            name = data[key]['name']
            if name.startswith(guac_user_prefix):
                guac_session.update_user_connection(name, key, "add", False)
                print(f"Associated Connection: {key} for User: {name}")

def guac_delete_conn():
        for user in range(0, guac_user_total):
            user = str(user)
            guac_session.delete_user(guac_user_prefix + user)
            print(f"Deleted User: {guac_user_prefix}{user}")

        response = guac_session.list_connections()
        data = json.loads(response)
        for key in data.keys():
            name = data[key]['name']
            if name.startswith(guac_user_prefix):
                guac_session.delete_connection(key)
                print(f"Deleted Connection: {key}")


def main():

    guac_session(guac_host, guac_datasource, guac_admin, guac_password)
    get_instances(guac_user_prefix, class_id)

    print(instances)

    # if guac_action == "create":





    # elif guac_action == "delete":




    # else:
    #     print("No Action Defined")

    guac_session.delete_token()

if __name__ == '__main__':
    main()