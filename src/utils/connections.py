"""
OpenStack and Guacamole connections
"""

import logging
from guacamole import session
from openstack import connect, enable_logging
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def openstack_connection(cloud,
                         openstack_clouds,
                         debug):
    """
    A function to establish a connection to OpenStack.

    Args:
        cloud (str): The name of the OpenStack cloud to connect to.
        openstack_clouds (dict): A dictionary containing OpenStack cloud information.
        debug (bool): A flag to enable debug logging.

    Returns:
        object: The connection object if successful, otherwise None.
    """
    # Enable debug logging if specified within the globals file

    endpoint = 'Connections'

    enable_logging(debug, debug)
    if debug:
        logging.getLogger("openstack").setLevel(logging.INFO)
        logging.getLogger("keystoneauth").setLevel(logging.INFO)
    else:
        logging.getLogger("openstack").setLevel(logging.CRITICAL)
        logging.getLogger("keystoneauth").setLevel(logging.CRITICAL)


    # Connect to OpenStack
    general_msg(f"Connecting to OpenStack cloud '{cloud}'...",
                endpoint)
    info_msg(f"Endpoint: {openstack_clouds['auth']['auth_url']}",
                endpoint,
                debug)
    openstack_connect = connect(cloud=cloud)
    if openstack_connect:
        success_msg("Connected to OpenStack",
                    endpoint)
    else:
        error_msg("Could not connect to OpenStack",
                  endpoint)

    return openstack_connect


def guacamole_connection(cloud,
                         guacamole_clouds,
                         debug):
    """
    A function to establish a connection with the Guacamole service.

    Args:
        guacamole_clouds (dict): A dictionary containing the information needed
        to connect to the Guacamole service.
        debug (bool): A flag indicating whether debug logging should be enabled.

    Returns:
        object: The connection object if successful, otherwise None.
    """
    # Enable debug logging if specified within the globals file

    endpoint = 'Connections'

    # Connect to Guacamole
    general_msg(f"Connecting to Guacamole cloud '{cloud}'...",
                endpoint)
    info_msg(f"Endpoint: {guacamole_clouds['host']}",
                endpoint,
                debug)
    guacamole_connect = session(guacamole_clouds['host'],
                                guacamole_clouds['data_source'],
                                guacamole_clouds['username'],
                                guacamole_clouds['password'])
    if guacamole_connect:
        success_msg("Connected to Guacamole",
                    endpoint)
    else:
        error_msg("Could not connect to Guacamole",
                  endpoint)

    return guacamole_connect
