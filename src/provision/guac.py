import time
import json
import orchestration.guac as guac
import orchestration.heat as heat
from utils.generate import generate_groups, generate_users, format_users, format_groups
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              user_params,
              debug):

    guac_params = {}
    guac_params['org_name'] = globals['org_name']
    guac_params['protocol'] = heat_params['conn_proto']['default']
    guac_params['password'] = heat_params['password']['default']
    guac_params['username'] = heat_params['username']['default']
    if user_params:
        guac_params['new_groups'] = format_groups(user_params,
                                                  debug)
        guac_params['new_users'] = format_users(user_params,
                                                debug)
    else:
        guac_params['new_groups'] = generate_groups(globals,
                                                    debug)
        guac_params['new_users'] = generate_users(globals,
                                                  guacamole_globals,
                                                  debug)
    guac_params['domain_name'] = guac.find_domain_name(heat_params,
                                                       debug)
    guac_params['parent_group_id'] = guac.get_conn_group_id(gconn,
                                                            guac_params['org_name'],
                                                            debug)
    guac_params['conn_groups'] = guac.get_groups(gconn,
                                                 guac_params['parent_group_id'],
                                                 debug)
    guac_params['conn_group_ids'] = guac.find_group_ids(guac_params['conn_groups'],
                                                        debug)
    guac_params['conn_users'] = guac.get_users(gconn,
                                               guac_params['org_name'],
                                               debug)
    guac_params['conn_list'] = guac.get_conns(gconn,
                                              guac_params['conn_group_ids'],
                                              debug)
    guac_params['instances'] = heat.get_ostack_instances(conn,
                                                         guac_params['new_groups'],
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
            guac.reprovision(gconn,
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
