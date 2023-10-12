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
        guac_params['recording'] = guacamole_globals['recording']
        guac_params['sharing'] = guacamole_globals['sharing']
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

        if guacamole_globals.get('mapped_only'):
            mapped_instances = []
            for data in guac_params['new_users'].values():
                mapped_instances.extend(data['instances'])
            mapped_instances = set(mapped_instances)

            guac_params['instances'] = [
                instance
                for instance in guac_params['instances']
                if instance['name'] in mapped_instances
                or 'guacd' in instance['name']
            ]

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
