"""
Handles the logic for provisioning Swift
"""
from objects.swift import SwiftContainer
from utils import msg_format, generate


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

    create, update = generate.set_provisioning_flags(globals_dict.get('provision'),
                                                     swift_globals.get('provision'),
                                                     swift_globals.get('update'),
                                                     endpoint,
                                                     debug)

    if create is None:
        msg_format.general_msg(f"Skipping {endpoint} provisioning.", endpoint)
        return

    # Backward compatibility
    if not swift_globals.get('assets_dir'):
        swift_globals['assets_dir'] = swift_globals.get('asset_dir')

    if not swift_globals.get('assets_dir'):
        msg_format.error_msg(f"The {endpoint} var 'assets_dir' is unset. Create and Update wont work.",
                             endpoint)
    assets_dir = swift_globals.get('assets_dir')

    if not swift_globals.get('pause'):
        msg_format.general_msg(f"The {endpoint} var 'pause' is unset. Using default pause of 0.5 seconds...",
                               endpoint)    
    pause = swift_globals.get('pause', 0.5)

    container_name = swift_globals.get(
        'container_name', globals_dict['organization']
    )

    container = SwiftContainer(conn,
                               container_name,
                               assets_dir,
                               debug)

    # Provision, deprovision, or reprovision
    if update:
        container.update(delay=pause)
    elif create:
        container.create(delay=pause)
    else:
        container.delete(delay=pause)

    msg_format.success_msg(f"{endpoint} provisioning complete.",
                           endpoint)
