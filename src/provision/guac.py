import orchestration.guac as guac
import time
from utils.generate import instances, users
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn, gconn, globals, guacamole_globals, heat_params, debug=False):
    try:
        users_list = users(globals['num_ranges'], globals['num_users'],
                                globals['range_name'], globals['user_name'], guacamole_globals['secure'], debug)
        instances_list = instances(globals['num_ranges'], globals['num_users'],
                                globals['range_name'], guacamole_globals['instance_mapping'], debug)

        openstack_instances = conn.list_servers()
        
        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(
                    f"Global provisioning is set to: {globals['provision']}", debug)
                general_msg("Provisioning Guacamole")
                guac.
                # provision = guac.provision(conn, name, dir, debug)
                # if provision:
                #     return provision
            elif not globals['provision']:
                general_msg("Deprovisioning Guacamole")
                # deprovision = guac.deprovision(conn, name, debug)
                # if deprovision:
                #     return deprovisionScreen Recording
        elif isinstance(guacamole_globals['provision'], bool):
            if guacamole_globals['provision']:
                info_msg(
                    f"Swift provisioning is set to: {globals['provision']}", debug)
                if isinstance(guacamole_globals['update'], bool):
                    if guacamole_globals['update']:
                        info_msg(
                            f"Swift update is set to: {globals['provision']}", debug)
                        general_msg("Updating Guacamole")
                        # deprovision = guac.deprovision(conn, name, debug)
                        # provision = guac.provision(conn, name, dir, debug)
                        # if deprovision and provision:
                        #     return provision+deprovision
                    else:
                        general_msg("Provisioning Guacamole")
                        # provision = guac.provision(conn, name, dir, debug)
                        # if provision:
                        #     return provision
                else:
                    general_msg("Provisioning Guacamole")
                    # provision = guac.provision(conn, name, dir, debug)
                    # if provision:
                    #     return provision
            elif not guacamole_globals['provision']:
                general_msg("Deprovisioning Guacamole")
                # deprovision = guac.deprovision(conn, name, debug)
                # if deprovision:
                #     return deprovision
        else:
            error_msg("Please check the provision parameter in globals.yaml")
            return None
    except Exception as e:
        error_msg(e)





    guac.provision(conn, gconn, globals, guacamole_globals, heat_params, users_list, instances_list, debug)

