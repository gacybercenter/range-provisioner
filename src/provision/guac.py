import time
import json
import orchestration.guac as guac
import orchestration.heat as heat
from utils.generate import generate_instance_names, generate_user_names, generate_group_names
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              debug):

    guac_params = {}
    guac_params['org_name'] = globals['org_name']
    guac_params['conn_proto'] = heat_params['conn_proto']['default']
    guac_params['heat_pass'] = heat_params['password']['default']
    guac_params['heat_user'] = heat_params['username']['default']
    guac_params['conn_groups'] = json.loads(gconn.list_connection_groups())
    guac_params['conn_list'] = json.loads(gconn.list_connections())
    # guac_params['users'] = list(json.loads(gconn.list_users()))
    guac_params['domain_name'] = guac.get_domain_name(heat_params,
                                                      debug)
    guac_params['instances'] = heat.get_ostack_instances(conn,
                                                         debug)
    guac_params['conn_group_id'] = guac.find_conn_group_id(guac_params['conn_groups'],
                                                          guac_params['org_name'],
                                                          debug)
    guac_params['child_groups'] = guac.find_child_groups(guac_params['conn_groups'],
                                                        guac_params['conn_group_id'],
                                                        debug)
    guac_params['new_users'] = generate_user_names(globals,
                                                   guacamole_globals,
                                                   debug)
    guac_params['new_groups'] = generate_group_names(globals,
                                                     guacamole_globals,
                                                     debug)

    if isinstance(globals['provision'], bool) and globals['provision']:
        info_msg(
            f"Global provisioning is set to: {globals['provision']}", debug)
        general_msg("Provisioning Guacamole")
        guac.provision(gconn,
                       guac_params,
                       debug)

    elif isinstance(globals['provision'], bool) and not globals['provision']:
        general_msg("Deprovisioning Guacamole")
        guac.deprovision(gconn,
                         guac_params,
                         debug)

    elif isinstance(guacamole_globals['provision'], bool) and guacamole_globals['provision']:
        info_msg(
            f"Guacamole provisioning is set to: {guacamole_globals['provision']}", debug)
        if isinstance(guacamole_globals['update'], bool) and guacamole_globals['update']:
            info_msg(
                f"Guacamole update is set to: {guacamole_globals['update']}", debug)
            general_msg("Updating Guacamole")
            guac.deprovision(gconn,
                             guac_params,
                             debug)
            guac.provision(gconn,
                           guac_params,
                           debug)

        else:
            general_msg("Provisioning Guacamole")
            guac.provision(gconn,
                           guac_params,
                           debug)

    elif isinstance(guacamole_globals['provision'], bool) and not guacamole_globals['provision']:
        general_msg("Deprovisioning Guacamole")
        guac.deprovision(gconn,
                         guac_params,
                         debug)

    else:
        error_msg("Please check the provision parameter in globals.yaml")
        return None
    # except Exception as error:
    #     error_msg(error)
