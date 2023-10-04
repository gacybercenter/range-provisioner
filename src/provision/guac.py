"""
Guacamole provisioning script.
Author: Marcus Corulli
Date: 09/28/2023
Version: 1.0

Description:
    Handles the logic for provisioning Guacamole
"""
import time
from orchestration import guac
from orchestration import heat
from utils.generate import generate_groups, generate_users, format_users, format_groups
from utils.msg_format import error_msg, info_msg, general_msg


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
                "Can't have provision: False, update: True in globals.yaml",
                endpoint
            )
            return

        info_msg(f"Guacamole provisioning is set to '{create}'",
                 endpoint,
                 debug)
        info_msg(f"Guacamole update is set to '{update}'",
                 endpoint,
                 debug)

    else:
        error_msg(
            "Please check the Guacamole provision and update parameters in globals.yaml",
            endpoint
        )
        return

    guac_params = {}

    guac_params['org_name'] = globals['org_name']
    guac_params['parent_group_id'] = guac.get_conn_group_id(gconn,
                                                            guac_params['org_name'],
                                                            debug)

    # Populate the guac_params for provision or reprovision
    if create or update:
        guac_params['protocol'] = heat_params['conn_proto']['default']
        guac_params['password'] = heat_params['password']['default']
        guac_params['username'] = heat_params['username']['default']
        # Format the users.yaml data into groups and users data
        if user_params:
            guac_params['new_groups'] = format_groups(user_params,
                                                      debug)
            guac_params['new_users'] = format_users(user_params,
                                                    debug)
        # If no users are specified, generate the groups and users data
        else:
            guac_params['new_groups'] = generate_groups(globals,
                                                        debug)
            guac_params['new_users'] = generate_users(globals,
                                                      guacamole_globals,
                                                      debug)
        guac_params['domain_name'] = guac.find_domain_name(heat_params,
                                                           debug)
        # Get the ostack instances, wait for them to get IP addresses if necessary
        ostack_complete = False
        while not ostack_complete:
            guac_params['instances'] = heat.get_ostack_instances(conn,
                                                                 guac_params['new_groups'],
                                                                 debug)
            for instance in guac_params['instances']:
                if not instance['hostname']:
                    general_msg(f"Waiting for {instance['name']} to get an IP address",
                                endpoint)
                    time.sleep(5)
                    continue

            ostack_complete = True

    # Populate the guac_params for deprovision or reprovision
    if not create or update:
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

    # Provision, deprovision, or reprovision
    if update:
        guac.reprovision(gconn,
                         guac_params,
                         debug)
    elif create:
        guac.provision(gconn,
                       guac_params,
                       debug)
    else:
        guac.deprovision(gconn,
                         guac_params,
                         debug)
