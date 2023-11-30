"""
Guacamole provisioning script.
Author: Marcus Corulli
Date: 09/28/2023
Version: 1.0

Description:
    Handles the logic for provisioning Guacamole
"""
from orchestration import guac
from utils.generate import generate_groups, generate_users, format_users, format_groups
from utils.msg_format import error_msg, info_msg


def provision(conn,
              gconn,
              globals,
              guacamole_globals,
              heat_params,
              user_params,
              debug):
    """
    Provisions or deprovisions Guacamole based on the given parameters.

    Args:
        conn (object): The Heat connection object.
        gconn (object): The Guacamole connection object.
        globals (dict): The globals dictionary.
        guacamole_globals (dict): The Guacamole globals dictionary.
        heat_params (dict): The Heat parameters.
        user_params (dict): The User parameters.
        debug (bool): The debug flag.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    # Set the create and update flags from the globals vars
    if isinstance(globals['provision'], bool):
        create = globals['provision']
        update = False
        info_msg(f"Global provisioning is set to {create}",
                 endpoint,
                 debug)

    # Set the create and update flags from the guacamole globals vars
    elif (isinstance(guacamole_globals['provision'], bool) and
          isinstance(guacamole_globals['update'], bool)):
        create = guacamole_globals['provision']
        update = guacamole_globals['update']

        if not create and update:
            error_msg(
                f"Can't have provision: False, update: True in {endpoint} globals.yaml",
                endpoint
            )
            return

        info_msg(f"{endpoint} provisioning is set to '{create}'",
                 endpoint,
                 debug)
        info_msg(f"{endpoint} update is set to '{update}'",
                 endpoint,
                 debug)

    else:
        error_msg(
            f"Please check the {endpoint} provison and update parameters in globals.yaml",
            endpoint
        )
        return

    guac_params = {}

    # Populate the guac_params
    guac_params['org_name'] = globals['org_name']
    guac_params['parent_group_id'] = guac.get_conn_id(gconn,
                                                      guac_params['org_name'],
                                                      'ROOT',
                                                      'group',
                                                      debug)
    # Populate the guac_params for provision or reprovision
    if create or update:
        guac_params['protocol'] = heat_params['conn_proto']['default']
        guac_params['username'] = heat_params['username']['default']
        guac_params['password'] = heat_params['password']['default']
        guac_params['domain_name'] = guac.find_domain_name(heat_params,
                                                           debug)
        guac_params['mapped_only'] = guacamole_globals['mapped_only']
        guac_params['recording'] = guacamole_globals['recording']
        guac_params['sharing'] = guacamole_globals['sharing']

    # Format the users.yaml data into groups and users data
    if user_params:
        guac_params['new_groups'] = format_groups(user_params,
                                                    debug)
        guac_params['instances'] = guac.get_heat_instances(conn,
                                                            guac_params,
                                                            debug) if create else []
        guac_params['new_users'] = format_users(user_params,
                                                guac_params,
                                                debug)
    # If no users are specified, generate the groups and users data
    else:
        guac_params['new_groups'] = generate_groups(globals,
                                                    debug)
        guac_params['instances'] = guac.get_heat_instances(conn,
                                                            guac_params,
                                                            debug) if create else []
        guac_params['new_users'] = generate_users(globals,
                                                    guac_params,
                                                    debug)
    if create and guac_params['mapped_only']:
        guac_params['instances'] = guac.reduce_heat_instances(guac_params,
                                                                debug)
    # Populate the guac_params with current connection and user data
    guac_params['conns'] = guac.get_conns(gconn,
                                          guac_params['parent_group_id'],
                                          debug)

    guac_params['users'] = guac.get_users(gconn,
                                          guac_params['org_name'],
                                          debug)

    # Provision, deprovision, or reprovision
    if create:
        guac.provision(gconn,
                       guac_params,
                       update,
                       debug)
    else:
        guac.deprovision(gconn,
                         guac_params)
