import orchestration.heat as heat
import time
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def provision(conn, globals, heat_globals, heat_params, sec_params, debug=False):
    try:
        stack_name = globals['range_name']
        template_dir = heat_globals['template_dir']
        update = heat_globals['update']
        last_stack = False
        if heat_params:
            heat_params = {k: v['default'] for k, v in heat_params.items() if 'default' in v}
        
        if sec_params:
            sec_params = {k: v['default'] for k, v in sec_params.items() if 'default' in v}

        if isinstance(globals['provision'], bool):
            if globals['provision']:
                info_msg(
                    f"Global provisioning is set to: {globals['provision']}", debug)

                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['sec']:
                        dir = f"{template_dir}/sec.yaml"
                        parameters = sec_params
                        name = f"{stack_name}-sec"
                        last_stack = True
                        heat.provision(conn, name, dir, parameters,
                                       last_stack, update, debug)
                else:
                    error_msg(
                        "Please check the provision parameter in globals.yaml")
                    return None

                last_stack = False

                if isinstance(heat_globals['main'], bool):
                    if heat_globals['main']:
                        dir = f"{template_dir}/main.yaml"
                        parameters = heat_params
                        parameters['container_name'] = stack_name
                        parameters['count'] = globals['num_users']

                        if globals['num_ranges'] > 1:
                            for i in range(globals['num_ranges']):
                                time.sleep(heat_globals['pause'])
                                name = f"{stack_name}{i+1}"
                                if i == globals['num_ranges']-1:
                                    last_stack = True
                                heat.provision(
                                    conn, name, dir, parameters, last_stack, update, debug)
                        else:
                            last_stack = True
                            heat.provision(
                                conn, name, dir, parameters, last_stack, update, debug)
                else:
                    error_msg(
                        "Please check the provision parameter in globals.yaml")
                    return None
                return True
            elif not globals['provision']:
                if isinstance(heat_globals['main'], bool):
                    if heat_globals['main']:
                        if globals['num_ranges'] > 1:
                            for i in range(globals['num_ranges']):
                                time.sleep(heat_globals['pause'])
                                name = f"{stack_name}{i+1}"
                                if i == globals['num_ranges']-1:
                                    last_stack = True
                                heat.deprovision(
                                    conn, name, last_stack, debug)
                        else:
                            name = stack_name
                            last_stack = True
                            heat.deprovision(conn, name, last_stack, debug)
                else:
                    error_msg(
                        "Please check the provision parameter in globals.yaml")
                    return None

                if isinstance(heat_globals['sec'], bool):
                    if heat_globals['sec']:
                        name = f"{stack_name}-sec"
                        last_stack = True
                        heat.deprovision(conn, name, last_stack, debug)
                else:
                    error_msg(
                        "Please check the provision parameter in globals.yaml")
                    return None
                return True
        else:
            if isinstance(heat_globals['provision'], bool):
                if heat_globals['provision']:
                    info_msg(
                        f"Heat global provisioning is set to: {heat_globals['provision']}", debug)

                    if isinstance(heat_globals['sec'], bool):
                        if heat_globals['sec']:
                            dir = f"{template_dir}/sec.yaml"
                            parameters = sec_params
                            name = f"{stack_name}-sec"
                            last_stack = True
                            heat.provision(conn, name, dir, parameters,
                                        last_stack, update, debug)
                    else:
                        error_msg(
                            "Please check the provision parameter in globals.yaml")
                        return None

                    last_stack = False

                    if isinstance(heat_globals['main'], bool):
                        if heat_globals['main']:
                            dir = f"{template_dir}/main.yaml"
                            parameters = heat_params
                            parameters['container_name'] = stack_name
                            parameters['count'] = globals['num_users']

                            if globals['num_ranges'] > 1:
                                for i in range(globals['num_ranges']):
                                    time.sleep(heat_globals['pause'])
                                    name = f"{stack_name}{i+1}"
                                    if i == globals['num_ranges']-1:
                                        last_stack = True
                                    heat.provision(
                                        conn, name, dir, parameters, last_stack, update, debug)
                            else:
                                last_stack = True
                                name = stack_name
                                heat.provision(
                                    conn, name, dir, parameters, last_stack, update, debug)
                    else:
                        error_msg(
                            "Please check the provision parameter in globals.yaml")
                        return None
                    return True
                elif not heat_globals['provision']:
                    if isinstance(heat_globals['main'], bool):
                        if heat_globals['main']:
                            if globals['num_ranges'] > 1:
                                for i in range(globals['num_ranges']):
                                    time.sleep(heat_globals['pause'])
                                    name = f"{stack_name}{i+1}"
                                    if i == globals['num_ranges']-1:
                                        last_stack = True
                                    heat.deprovision(
                                        conn, name, last_stack, debug)
                            else:
                                last_stack = True
                                name = stack_name
                                heat.deprovision(conn, name, last_stack, debug)
                    else:
                        error_msg(
                            "Please check the provision parameter in globals.yaml")
                        return None

                    if isinstance(heat_globals['sec'], bool):
                        if heat_globals['sec']:
                            name = f"{stack_name}-sec"
                            last_stack = True
                            heat.deprovision(conn, name, last_stack, debug)
                    else:
                        error_msg(
                            "Please check the provision parameter in globals.yaml")
                        return None
                    return True

    except Exception as e:
        error_msg(e)
