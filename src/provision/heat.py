"""
Handles the logic for provisioning Heat
"""
import os
from time import sleep
from yaml import dump
from tempfile import NamedTemporaryFile
from objects.heat import HeatStack
from utils import msg_format, generate, heat_environment, load_template


def provision(conn: object,
              globals_dict: dict,
              heat_globals: dict,
              debug: bool = False,
              dry_run: bool = False) -> None:
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

    multi_stack_environment = generate.read_multi_stack_environment()
    if multi_stack_environment['num_ranges'] > 1:
        stack_name = (
            multi_stack_environment['org_name']
            or heat_globals.get('stack_name')
        )
    else:
        stack_name = (
            heat_globals.get('stack_name')
            or multi_stack_environment['org_name']
        )

    if not stack_name:
        stack_name = globals_dict.get('organization')
    if not stack_name:
        raise ValueError(
            "Heat stack name is unset and no organization name is configured."
        )

    amount = heat_globals['amount'] if 'amount' in heat_globals else globals_dict.get(
        'amount', 1
    )
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
        raise ValueError("Heat 'amount' must be a positive integer.")
    stack_names = generate.generate_names(amount,
                                          stack_name)

    if not heat_globals.get('heat_file'):
        raise ValueError("Heat 'heat_file' is required.")
    heat_file = heat_globals.get('heat_file')
    template_dir = globals_dict.get('template_dir')

    if 'pause' not in heat_globals:
        msg_format.general_msg(f"The {endpoint} var 'pause' is unset. Using default pause of 0.5 seconds...",
                               endpoint)
    pause = heat_globals.get('pause', 0.5)

    if 'stack_delay' not in heat_globals:
        msg_format.general_msg(f"The {endpoint} var 'stack_delay' is unset. Using default stack delay of 30 seconds...",
                               endpoint)
    stack_delay = heat_globals.get('stack_delay', 30)
    for name, value in (('pause', pause), ('stack_delay', stack_delay)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Heat '{name}' must be a non-negative number.")

    heat_data = load_template.load_yaml_file(heat_file,
                                             template_dir,
                                             debug)
    heat_params = heat_data.get('parameters', {})
    env_file = heat_globals.get('env_file')
    env_stacks = heat_globals.get('env_stacks', [])
    if not isinstance(env_stacks, list) or not all(
        isinstance(stack, str) and stack.strip() for stack in env_stacks
    ):
        raise ValueError("Heat 'env_stacks' must be a list of nonempty stack names.")
    if env_stacks and not env_file:
        raise ValueError("Heat 'env_stacks' requires 'env_file'.")
    if env_file is not None and (not isinstance(env_file, str) or not env_file.strip()):
        raise ValueError("Heat 'env_file' must be a nonempty filename.")
    env_parameters = None
    if env_file and (create or update):
        env_parameters = heat_environment.load_parameters(
            conn, env_file, template_dir, env_stacks
        )
    updated_heat_params = generate.update_heat_params(heat_globals,
                                                      heat_params,
                                                      endpoint,
                                                      debug,
                                                      multi_stack_environment,
                                                      env_parameters)

    if not heat_globals.get('jinja'):
        msg_format.general_msg(f"The {endpoint} var 'jinja' is unset. Using default False...",
                               endpoint)
    jinja = heat_globals.get('jinja', False)

    temp_heat_file = None
    try:
        if jinja and not dry_run:
            msg_format.general_msg(f"Using Jinja for {endpoint} template.",
                                   endpoint)
            with NamedTemporaryFile(
                'w',
                delete=False,
                suffix='.yaml',
                encoding='utf-8'
            ) as temp_file:
                temp_heat_file = temp_file.name
                dump(heat_data, temp_file)
                temp_file.flush()
            msg_format.info_msg(f"Created temporary Jinja file '{temp_heat_file}'.",
                                endpoint,
                                debug)
            template_file = temp_heat_file
        else:
            template_file = heat_file

        for index, stack_name in enumerate(stack_names):
            stack = HeatStack(conn,
                              stack_name,
                              template_file,
                              updated_heat_params,
                              debug,
                              resolve_outputs=False)
            if dry_run:
                action = 'update' if update else 'create' if create else 'delete'
                msg_format.general_msg(
                    f"DRY RUN: Would {action} Heat stack '{stack_name}'.",
                    endpoint
                )
                continue
            if update:
                stack.update(delay=pause)
            elif create:
                stack.create(delay=pause)
            else:
                stack.delete(delay=pause)

            if stack_delay > 0 and index < len(stack_names) - 1:
                msg_format.general_msg(f"Pausing for {stack_delay} seconds...",
                                       endpoint)
                sleep(stack_delay)
    finally:
        if temp_heat_file and os.path.exists(temp_heat_file):
            os.remove(temp_heat_file)
            msg_format.info_msg(f"Deleted temporary Jinja file '{temp_heat_file}'.",
                                endpoint,
                                debug)

    if dry_run:
        msg_format.general_msg(f"{endpoint} dry run complete.",
                               endpoint)
    else:
        msg_format.success_msg(f"{endpoint} provisioning complete.",
                               endpoint)
