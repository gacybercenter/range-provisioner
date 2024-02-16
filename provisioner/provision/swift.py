"""
Handles the logic for provisioning Swift
"""
import orchestration.swift as swift
from utils.msg_format import error_msg, info_msg


def provision(conn: object,
              globals: dict,
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

    # Set the create and update flags from the globals vars
    if isinstance(globals['provision'], bool):
        create = globals['provision']
        update = swift_globals.get('update', False)
        info_msg(f"Global provisioning is set to '{create}'",
                 endpoint,
                 debug)

    # Set the create and update flags from the swift globals vars
    elif (isinstance(swift_globals['provision'], bool) and
          isinstance(swift_globals['update'], bool)):
        create = swift_globals['provision']
        update = swift_globals['update']

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

    range_name = globals['range_name']
    directory = swift_globals['asset_dir']

    # Provision, deprovision, or reprovision
    if update:
        swift.deprovision(conn,
                          range_name,
                          debug)
        swift.provision(conn,
                        range_name,
                        directory,
                        debug)
    elif create:
        swift.provision(conn,
                        range_name,
                        directory,
                        debug)
    else:
        swift.deprovision(conn,
                          range_name,
                          debug)
