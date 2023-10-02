"""
Handles the logic for provisioning Heat
"""
import time
from orchestration import heat
from utils.msg_format import error_msg, info_msg, general_msg
from utils.generate import generate_names


def provision(conn: object,
              globals: dict,
              heat_globals: dict,
              heat_params: dict,
              sec_params: dict,
              debug=False) -> bool:
    """ Provisions or deprovisions Heat based on the given parameters. """

    # Set the create and update flags from the globals vars
    if isinstance(globals['provision'], bool):
        create = globals['provision']
        update = False
        info_msg("Global provisioning is set to: "
                 f"{create}", debug)

    # Set the create and update flags from the heat globals vars
    elif isinstance(heat_globals['provision'], bool) and isinstance(heat_globals['update'], bool):
        create = heat_globals['provision']
        update = heat_globals['update']

        if not create and update:
            error_msg(
                "Heat ERROR:  Can't have "
                "provision: False, update: True in globals.yaml"
            )
            return

        info_msg("Heat provisioning is set to: "
                 f"{create}", debug)
        info_msg("Heat update is set to: "
                 f"{update}", debug)

    else:
        error_msg(
            "Heat ERROR:  Please check the Heat"
            "provison and update parameters in globals.yaml"
        )
        return

    # Format the parameters for Heat
    if heat_params:
        heat_params = {
            k: v['default']
            for k, v in heat_params.items()
            if 'default' in v
        }

    if sec_params:
        sec_params = {
            k: v['default']
            for k, v in sec_params.items()
            if 'default' in v
        }

    heat_params['container_name'] = globals['range_name']
    heat_params['instance_name'] = globals['user_name']
    heat_params['count'] = globals['num_users']
    stack_names = generate_names(globals['num_ranges'],
                                 heat_params['container_name'])

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
            time.sleep(heat_globals['pause'])
        else:
            general_msg("No security group parameters were provided")
        for name in stack_names:
            last_stack = name == stack_names[-1]
            heat.provision(conn,
                           name,
                           f"{heat_globals['template_dir']}/main.yaml",
                           heat_params,
                           last_stack,
                           update,
                           debug)
            time.sleep(heat_globals['pause'])
    else:
        for name in stack_names:
            last_stack = name == stack_names[-1]
            heat.deprovision(conn,
                             name,
                             last_stack,
                             debug)
            time.sleep(heat_globals['pause'])
