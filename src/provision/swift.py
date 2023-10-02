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
    # Set the create and update flags from the globals vars
    if isinstance(globals['provision'], bool):
        create = globals['provision']
        update = False
        info_msg("Global provisioning is set to: "
                 f"{create}", debug)

    # Set the create and update flags from the guacamole globals vars
    elif isinstance(swift_globals['provision'], bool) and isinstance(swift_globals['update'], bool):
        create = swift_globals['provision']
        update = swift_globals['update']

        if not create and update:
            error_msg(
                "Swift ERROR:  Can't have "
                "provision: False, update: True in globals.yaml"
            )
            return

        info_msg("Swift provisioning is set to: "
                 f"{create}", debug)
        info_msg("Swift update is set to: "
                 f"{update}", debug)

    else:
        error_msg(
            "Swift ERROR:  Please check the Swift"
            "provison and update parameters in globals.yaml"
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
