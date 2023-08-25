import time
import orchestration.guac as guac
import orchestration.heat as heat
from utils.generate import generate_instance_names, generate_user_names
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              debug=False):

    guac_params = guacamole_globals
    guac_params['guacd'] = globals['guacd']
    guac_params['conn_proto'] = heat_params['conn_proto']['default']
    guac_params['username'] = heat_params['username']['default']
    guac_params['password'] = heat_params['password']['default']
    guac_params['instances'] = heat.get_ostack_instances(conn,
                                                         debug)
    guac_params['new_instances'] = generate_instance_names(globals,
                                                           guacamole_globals,
                                                           debug)
    guac_params['users'] = guac.get_existing_accounts(gconn,
                                                      debug)
    guac_params['new_users'] = generate_user_names(globals,
                                                   guacamole_globals,
                                                   debug)
    guac_params['conn_groups'] = guac.get_conn_groups(gconn,
                                                      debug)
    guac_params['conn_group_id'] = guac.get_conn_group_id(gconn,
                                                          guac_params['conn_group_name'],
                                                          debug)[0]

    # general_msg(guac_params)

    if isinstance(globals['provision'], bool) and globals['provision']:
        info_msg(
            f"Global provisioning is set to: {globals['provision']}", debug)
        general_msg("Provisioning Guacamole")
        guac.provision(gconn,
                       guac_params,
                       debug=False)

    elif isinstance(globals['provision'], bool) and not globals['provision']:
        general_msg("Deprovisioning Guacamole")
        guac.deprovision(gconn,
                         guac_params,
                         debug=False)

    elif isinstance(guacamole_globals['provision'], bool) and guacamole_globals['provision']:
        info_msg(
            f"Guacamole provisioning is set to: {guacamole_globals['provision']}", debug)
        if isinstance(guacamole_globals['update'], bool) and guacamole_globals['update']:
            info_msg(
                f"Guacamole update is set to: {guacamole_globals['update']}", debug)
            general_msg("Updating Guacamole")
            guac.deprovision(gconn,
                             guac_params,
                             debug=False)
            guac.provision(gconn,
                           guac_params,
                           debug=False)

        else:
            general_msg("Provisioning Guacamole")
            guac.provision(gconn,
                           guac_params,
                           debug=False)

    elif isinstance(guacamole_globals['provision'], bool) and not guacamole_globals['provision']:
        general_msg("Deprovisioning Guacamole")
        guac.deprovision(gconn,
                         guac_params,
                         debug=False)

    else:
        error_msg("Please check the provision parameter in globals.yaml")
        return None
    # except Exception as error:
    #     error_msg(error)
