import orchestration.guac as guac
import time
from utils.generate import instances, users
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn, gconn, globals, guacamole_globals, heat_params, debug=False):

    guac.provision(conn, gconn, globals, guacamole_globals, heat_params, debug)

    # instance_list = conn.list_servers()
    # print(instance_list)

    # user_list = gconn.list_users()
    # print(user_list)


# TODO(chateaulav): Everything below this point is a work in progress
#                   and is not currently functional. It belonged to the
#                   original guac.py file and is being moved here for
#                   reference purposes.

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
    usernames = create_usernames(
        global_dict['num_users'], global_dict['username_prefix'])
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
