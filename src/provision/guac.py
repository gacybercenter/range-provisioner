"""
Guacamole provisioning script
Author: Marcus Corulli
Date: 5/1/2024
Version: 2.0

Description:
    Handles the logic for provisioning Guacamole
"""
from utils.generate import set_provisioning_flags
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
        oconn (object): The Heat connection object.
        gconn (object): The Guacamole connection object.
        globals_dict (dict): The globals dictionary.
        guacamole_globals (dict): The Guacamole globals dictionary.
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

    organization = globals_dict['organization']
    delay = guacamole_globals['pause']

    new_conns = NewConnections(gconn,
                               oconn,
                               conn_params,
                               organization,
                               debug)

    # if update:
    #     new_conns.update(delay)
    # elif create:
    #     new_conns.create(delay)
    # else:
    #     new_conns.delete(delay)

    new_users = NewUsers(gconn,
                         conn_params,
                         organization,
                         new_conns.connections,
                         debug)

    # if update:
    #     new_users.update(delay)
    # elif create:
    #     new_users.create(delay)
    # else:
    #     new_users.delete(delay)
