"""
Handles the logic for provisioning Heat
"""
import time
from orchestration import heat
from utils.msg_format import error_msg, info_msg, general_msg
from utils.generate import generate_names, set_provisioning_flags


def provision(conn: object,
              globals_dict: dict,
              heat_globals: dict,
              heat_params: dict,
              sec_params: dict,
              debug=False) -> bool:
    """ Provisions or deprovisions Heat based on the given parameters. """

    endpoint = 'Heat'

    create, update = set_provisioning_flags(globals_dict.get('provision'),
                                            heat_globals.get('provision'),
                                            heat_globals.get('update'),
                                            endpoint,
                                            debug)

    stack_names = generate_names(globals_dict['amount'],
                                 globals_dict['organization'])
    pause = heat_globals.get('pause', 0)

    # Format the parameters for Heat
    if heat_params:
        heat_params = {
            k: v['default']
            for k, v in heat_params.items()
            if 'default' in v
        }

    if 'parameters' in heat_globals and isinstance(heat_globals['parameters'], list):
        for parameter in heat_globals['parameters']:
            for key, value in parameter.items():
                if key not in heat_params:
                    error_msg(
                        f"Did not update parameter '{key}'. Not found in the main.yaml file.",
                        endpoint
                    )
                    continue
                heat_params[key] = value
                info_msg(
                    f"Updated parameter '{key}' with value '{value}'.",
                    endpoint,
                    debug
                )

    if sec_params:
        sec_params = {
            k: v['default']
            for k, v in sec_params.items()
            if 'default' in v
        }

    # Provision, deprovision, or reprovision
    if create:
        if sec_params:
            name = heat_params['container_name']
            heat.provision(conn,
                           f"{name}-sec",
                           f"{heat_globals['template_dir']}/sec.yaml",
                           sec_params,
                           True,
                           update,
                           debug)
            time.sleep(pause)
        else:
            general_msg("No security group parameters were provided",
                        endpoint)
        for name in stack_names:
            last_stack = name == stack_names[-1]
            heat.provision(conn,
                           name,
                           f"{heat_globals['template_dir']}/main.yaml",
                           heat_params,
                           last_stack,
                           update,
                           debug)
            time.sleep(pause)
    else:
        for name in stack_names:
            last_stack = name == stack_names[-1]
            heat.deprovision(conn,
                             name,
                             last_stack,
                             debug)
            time.sleep(pause)
