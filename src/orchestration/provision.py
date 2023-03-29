import orchestration.heat as heat
import orchestration.guacamole as guac
import orchestration.swift as swift
import time
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def object_store(conn, globals, swift_globals, debug=False):
    try:
        name = globals['range_name']
        dir = swift_globals['asset_dir']
        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(f"Global provisioning is set to: {globals['provision']}", debug)
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
                    info_msg(f"Swift provisioning is set to: {globals['provision']}", debug)
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


def range(conn, globals, heat_globals, heat_params, sec_params, debug=False):
    try:
        name = globals['range_name']
        dir = heat_globals['template_dir']
        update = heat_globals['update']
        last_stack = False


        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(f"Global provisioning is set to: {globals['provision']}", debug)
                
                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['sec']:
                        dir = f"{dir}/sec.yaml"
                        parameters = sec_params
                        name = f"{name}-sec"
                        heat.provision(conn, name, dir, parameters, last_stack, update, debug)
                else:
                    error_msg("Please check the provision parameter in globals.yaml")
                    return None
                
                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['main']:
                        dir = f"{dir}/main.yaml"
                        parameters = heat_params
                        parameters['container_name'] = name
                        parameters['count'] = globals['num_users']

                        if globals['num_ranges'] > 1:
                            for i in range(globals['num_ranges']):
                                time.sleep(heat_globals['sleep'])
                                parameters['range_name'] = f"{name}-{i}"
                                if i == globals['num_ranges']-1:
                                    last_stack = True
                            heat.provision(conn, name, dir, parameters, last_stack, update, debug)
                    return True
                else:
                    error_msg("Please check the provision parameter in globals.yaml")
                    return None

            elif not globals['provision']:
                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['sec']:
                        name = f"{name}-sec"
                        heat.deprovision(conn, name, debug)
                else:
                    error_msg("Please check the provision parameter in globals.yaml")
                    return None
                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['main']:
                        if globals['num_ranges'] > 1:
                            for i in range(globals['num_ranges']):
                                name = f"{name}-{i}"
                                if i == globals['num_ranges']-1:
                                    last_stack = True
                                deprovision = heat.deprovision(conn, name, last_stack, debug)
                        else:
                            heat.deprovision(conn, name, debug)
                else:
                    error_msg("Please check the provision parameter in globals.yaml")
                    return None
                return True
        else:
            if isinstance(heat_globals['provision'], bool):
                if heat_globals['provision']:
                    info_msg(f"Global provisioning is set to: {heat_globals['provision']}", debug)

                    if isinstance(heat_globals['sec'], bool):
                        if heat_globals['sec']:
                            dir = f"{dir}/sec.yaml"
                            parameters = sec_params
                            name = f"{name}-sec"
                            heat.provision(conn, name, dir, parameters, last_stack, update, debug)
                    else:
                        error_msg("Please check the provision parameter in globals.yaml")
                        return None

                    if isinstance(heat_globals['sec'], bool):
                        if heat_globals['main']:
                            dir = f"{dir}/main.yaml"
                            parameters = heat_params
                            parameters['container_name'] = name

                            if globals['num_ranges'] > 1:
                                for i in range(globals['num_ranges']):
                                    time.sleep(heat_globals['sleep'])
                                    parameters['range_name'] = f"{name}-{i}"
                                    if i == globals['num_ranges']-1:
                                        last_stack = True
                                heat.provision(conn, name, dir, parameters, last_stack, update, debug)
                    else:
                        error_msg("Please check the provision parameter in globals.yaml")
                        return None

                elif not heat_globals['provision']:
                    if heat_globals['sec']:
                        name = f"{name}-sec"
                        heat.deprovision(conn, name, debug)
                    if heat_globals['main']:
                        if globals['num_ranges'] > 1:
                            for i in range(globals['num_ranges']):
                                name = f"{name}-{i}"
                                if i == globals['num_ranges']-1:
                                    last_stack = True
                                deprovision = heat.deprovision(conn, name, last_stack, debug)
                        else:
                            deprovision = heat.deprovision(conn, name, debug)
                    return deprovision
            else:
                error_msg("Please check the provision parameter in globals.yaml")
                return None

    except Exception as e:
        error_msg(e)

def guacamole(conn, globals, heat_params, sec_params, debug=False):
    name = globals['range_name']