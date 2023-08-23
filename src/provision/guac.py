import time
import orchestration.guac as guac
from utils.generate import generate_instance_names, generate_user_names
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              debug=False):
    try:
        user_names = generate_user_names(globals['num_ranges'],
                                         globals['num_users'],
                                         globals['range_name'],
                                         globals['user_name'],
                                         guacamole_globals['secure'],
                                         debug)
        instance_names = generate_instance_names(globals['num_ranges'],
                                                 globals['num_users'],
                                                 globals['range_name'],
                                                 guacamole_globals['instance_mapping'],
                                                 debug)

        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(
                    f"Global provisioning is set to: {globals['provision']}", debug)
                general_msg("Provisioning Guacamole")

                provision = guac.provision(conn,
                                           gconn,
                                           guacamole_globals,
                                           heat_params,
                                           user_names,
                                           instance_names,
                                           debug=False)
                if provision:
                    return provision
            elif not globals['provision']:
                general_msg("Deprovisioning Guacamole")
                deprovision = guac.deprovision(gconn,
                                               guacamole_globals,
                                               user_names,
                                               debug=False)
                if deprovision:
                    return deprovision
        elif isinstance(guacamole_globals['provision'], bool):
            if guacamole_globals['provision']:
                info_msg(
                    f"Guacamole provisioning is set to: {globals['provision']}", debug)
                if isinstance(guacamole_globals['update'], bool):
                    if guacamole_globals['update']:
                        info_msg(
                            f"Guacamole update is set to: {globals['provision']}", debug)
                        general_msg("Updating Guacamole")
                        deprovision = guac.deprovision(gconn,
                                                       guacamole_globals,
                                                       user_names,
                                                       debug=False)
                        provision = guac.provision(conn,
                                                   gconn,
                                                   guacamole_globals,
                                                   heat_params,
                                                   user_names,
                                                   instance_names,
                                                   debug=False)
                        if deprovision and provision:
                            return provision+deprovision
                    else:
                        general_msg("Provisioning Guacamole")
                        provision = guac.provision(conn,
                                                   gconn,
                                                   guacamole_globals,
                                                   heat_params,
                                                   user_names,
                                                   instance_names,
                                                   debug=False)
                        if provision:
                            return provision
                else:
                    general_msg("Provisioning Guacamole")
                    provision = guac.provision(conn,
                                               gconn,
                                               guacamole_globals,
                                               heat_params,
                                               user_names,
                                               instance_names,
                                               debug=False)
                    if provision:
                        return provision
            elif not guacamole_globals['provision']:
                general_msg("Deprovisioning Guacamole")
                deprovision = guac.deprovision(gconn,
                                               guacamole_globals,
                                               user_names,
                                               debug=False)
                if deprovision:
                    return deprovision
        else:
            error_msg("Please check the provision parameter in globals.yaml")
            return None
    except Exception as error:
        error_msg(error)
