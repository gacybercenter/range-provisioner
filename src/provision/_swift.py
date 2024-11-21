"""
Handles the logic for provisioning Swift
"""
import orchestration.swift as swift
from utils.generate import set_provisioning_flags
from utils import msg_format

def provision(conn: object,
              globals_dict: dict,
              swift_globals: dict,
              debug=False) -> None:
    """
    Provisions or deprovisions Swift based on the given parameters.

    Args:
        conn (object): The Heat connection object.
        globals (dict): The globals dictionary.
        swift_globals (dict): The Swift globals dictionary.
        debug (bool): The debug flag.

    Returns:
        None
    """

    endpoint = 'Swift'

    create, update = set_provisioning_flags(globals_dict.get('provision'),
                                            swift_globals.get('provision'),
                                            swift_globals.get('update'),
                                            endpoint,
                                            debug)

    if create is None:
        msg_format.general_msg(f"Skipping {endpoint} provisioning.", endpoint)
        return

    directory = swift_globals['asset_dir']
    container_name = swift_globals.get('container_name', globals_dict['organization'])
    # pause = swift_globals.get('pause', 0)

    # Provision, deprovision, or reprovision
    if update:
        swift.deprovision(conn,
                          container_name,
                          debug)
        swift.provision(conn,
                        container_name,
                        directory,
                        debug)
    elif create:
        swift.provision(conn,
                        container_name,
                        directory,
                        debug)
    else:
        swift.deprovision(conn,
                          container_name,
                          debug)

    msg_format.success_msg(f"Provisioning {endpoint} Complete",
                           endpoint)
