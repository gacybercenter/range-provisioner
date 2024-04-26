"""
Guacamole provisioning script.
Author: Marcus Corulli
Date: 09/28/2023
Version: 1.0

Description:
    Handles the logic for provisioning Guacamole
"""
from orchestration import guac
from utils.generate import set_provisioning_flags, get_conn_id
from utils.msg_format import error_msg, info_msg
from objects.users import NewUsers
from objects.connections import NewConnections

def provision(oconn: object,
              gconn: object,
              globals_dict: dict,
              guacamole_globals: dict,
              conn_params: dict,
              debug: bool):
    """
    Provisions or deprovisions Guacamole based on the given parameters.

    Args:
        conn (object): The Heat connection object.
        gconn (object): The Guacamole connection object.
        globals_dict (dict): The globals dictionary.
        guacamole_globals (dict): The Guacamole globals dictionary.
        heat_params (dict): The Heat parameters.
        conn_params (dict): The User parameters.
        debug (bool): The debug flag.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    create, update = set_provisioning_flags(globals_dict.get('provision'),
                                            guacamole_globals.get('provision'),
                                            guacamole_globals.get('update'),
                                            endpoint,
                                            debug)

    # Populate the guac_params
    organization = globals_dict['organization']

    users = guacamole_globals['users']
    pause = guacamole_globals['pause']

    new_conns = NewConnections(gconn,
                              oconn,
                              conn_params,
                              organization,
                              debug)
    new_users = NewUsers(gconn,
                         conn_params,
                         organization,
                         new_conns.connections,
                         debug)
