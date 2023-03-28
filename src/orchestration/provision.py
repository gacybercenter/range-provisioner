import orchestration.heat as heat
import orchestration.guacamole as guac
import orchestration.swift as swift
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def object_store(conn, globals, swift_globals, debug=False):
    try:
        name = globals['range_name']
        dir = swift_globals['asset_dir']
        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(f"Global provsioning is set to: {globals['provision']}", debug)
                provision = swift.provision(conn, name, dir, debug)
                if provision:
                    return provision
            elif not globals['provision']:
                deprovision = swift.deprovision(conn, name, debug)
                if deprovision:
                    return deprovision
        else:
            if isinstance(swift_globals['provision'], bool):
                if swift_globals['provision']:
                    info_msg(f"Swift provsioning is set to: {globals['provision']}", debug)
                    if isinstance(swift_globals['update'], bool):
                        if swift_globals['update']:
                            info_msg(f"Swift update is set to: {globals['provision']}", debug)
                            deprovision = swift.deprovision(conn, name, debug)
                            provision = swift.provision(conn, name, dir, debug)
                            if deprovision and provision:
                                return provision+deprovision
                        else:
                            provision = swift.provision(conn, name, dir, debug)
                            if provision:
                                return provision
                elif not swift_globals['provision']:
                    deprovision = swift.deprovision(conn, name, debug)
                    if deprovision:
                        return deprovision
            else:
                error_msg("Please check the provision parameter in globals.yaml")
                return None
    except Exception as e:
        error_msg(e)


def range(conn, gloabls, heat_params, sec_params, debug=False):
    name = globals['range_name']
    heat.search(conn, name)


def guacamole(conn, gloabls, heat_params, sec_params, debug=False):
    name = globals['range_name']