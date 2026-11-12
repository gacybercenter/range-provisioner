"""
Handles the logic for provisioning Heat
"""
import os
import re
from time import sleep
from yaml import dump
from tempfile import NamedTemporaryFile
from objects.heat import HeatStack
from utils import msg_format, generate, load_template

# Access environment variables specific to multi-stack enterprise deployments
num_ranges = os.getenv("num_ranges")
org_name = os.getenv("org_name")

def provision(conn: object,
              globals_dict: dict,
              heat_globals: dict,
              debug: bool = False) -> None:
    """
    Provisions or deprovisions Heat based on the given parameters.

    Args:
        conn (object): The Heat connection object.
        globals (dict): The globals dictionary.
        heat_globals (dict): The Heat globals dictionary.
        heat_data (dict): The Heat data dictionary.
        debug (bool): The debug flag.

    Returns:
        None
    """

    endpoint = 'Heat'

    create, update = generate.set_provisioning_flags(globals_dict.get('provision'),
                                                     heat_globals.get(
                                                         'provision'),
                                                     heat_globals.get(
                                                         'update'),
                                                     endpoint,
                                                     debug)

    if create is None:
        msg_format.general_msg(f"Skipping {endpoint} provisioning.", endpoint)
        return

    if num_ranges is None:
        stack_name = heat_globals.get('stack_name', org_name)
    elif int(num_ranges) == 1:
        stack_name = heat_globals.get('stack_name', org_name)
    elif int(num_ranges) > 1:
        stack_name = org_name

    if stack_name is None:
        if not heat_globals.get('stack_name'):
            organization = globals_dict.get('organization')
            msg_format.general_msg(f"The {endpoint} var 'stack_name' is unset. Using global organization '{organization}'...",
                                endpoint)
            heat_globals['stack_name'] = organization
            stack_name = organization
        else:
            stack_name = heat_globals['stack_name']

    if not stack_name:
        msg_format.error_msg(f"The {endpoint} var 'stack_name' is unset and no organization name found in environment variables.",
                            endpoint)
        return

    amount = heat_globals['amount'] if 'amount' in heat_globals else globals_dict.get(
        'amount', 1
    )
    stack_names = generate.generate_names(amount,
                                          stack_name)

    if not heat_globals.get('heat_file'):
        msg_format.error_msg(f"The {endpoint} var 'heat_file' is unset. Create and Update wont work.",
                             endpoint)
    heat_file = heat_globals.get('heat_file')
    template_dir = globals_dict.get('template_dir')

    if not heat_globals.get('pause'):
        msg_format.general_msg(f"The {endpoint} var 'pause' is unset. Using default pause of 0.5 seconds...",
                               endpoint)
    pause = heat_globals.get('pause', 0.5)

    if not heat_globals.get('stack_delay'):
        msg_format.general_msg(f"The {endpoint} var 'stack_delay' is unset. Using default stack delay of 30 seconds...",
                               endpoint)
    stack_delay = heat_globals.get('stack_delay', 30)

    heat_data = load_template.load_yaml_file(heat_file,
                                                template_dir,
                                                debug)
    heat_params = heat_data.get('parameters', {})
    updated_heat_params = generate.update_heat_params(heat_globals,
                                                      heat_params,
                                                      endpoint,
                                                      debug)

    if not heat_globals.get('jinja'):
        msg_format.general_msg(f"The {endpoint} var 'jinja' is unset. Using default False...",
                               endpoint)
    jinja = heat_globals.get('jinja', False)

    if jinja:
        msg_format.general_msg(f"Using Jinja for {endpoint} template.",
                               endpoint)
        with NamedTemporaryFile('w', delete=False, suffix='.yaml') as temp_file:
            dump(heat_data, temp_file)
            temp_file.flush()
            temp_heat_file = os.path.relpath(temp_file.name)
            msg_format.info_msg(f"Created temporary Jinja file '{temp_file.name}'.",
                                endpoint,
                                debug)
            for stack_name in stack_names:
                stack = HeatStack(conn,
                                  stack_name,
                                  temp_heat_file,
                                  updated_heat_params,
                                  debug)
                if update:
                    stack.update(delay=pause)
                elif create:
                    stack.create(delay=pause)
                else:
                    stack.delete(delay=pause)

                if stack_delay > 0 and stack_name != stack_names[-1]:
                    msg_format.general_msg(f"Pausing for {stack_delay} seconds...",
                                           endpoint)
                    sleep(stack_delay)
    
        os.remove(temp_file.name)
        msg_format.info_msg(f"Deleted temporary Jinja file '{temp_file.name}'.",
                            endpoint,
                            debug)
    else:
        for stack_name in stack_names:
            stack = HeatStack(conn,
                              stack_name,
                              heat_file,
                              updated_heat_params,
                              debug)
            if update:
                stack.update(delay=pause)
            elif create:
                stack.create(delay=pause)
            else:
                stack.delete(delay=pause)

            if stack_delay > 0 and stack_name != stack_names[-1]:
                msg_format.general_msg(f"Pausing for {stack_delay} seconds...",
                                       endpoint)
                sleep(stack_delay)

    msg_format.success_msg(f"{endpoint} provisioning complete.",
                           endpoint)
