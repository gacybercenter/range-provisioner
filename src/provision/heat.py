"""
Handles the logic for provisioning Heat
"""
from time import sleep
from objects.heat import HeatStack
from utils import msg_format, generate


def provision(conn: object,
              globals_dict: dict,
              heat_globals: dict,
              heat_params: dict,
              debug=False) -> None:
    """
    Provisions or deprovisions Heat based on the given parameters.

    Args:
        conn (object): The Heat connection object.
        globals (dict): The globals dictionary.
        heat_globals (dict): The Heat globals dictionary.
        heat_params (dict): The Heat parameters dictionary.
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

    if not heat_globals.get('heat_file'):
        msg_format.error_msg(f"The {endpoint} var 'heat_file' is unset. Create and Update wont work.",
                             endpoint)
    heat_file = heat_globals.get('heat_file')

    if not heat_globals.get('pause'):
        msg_format.general_msg(f"The {endpoint} var 'pause' is unset. Using default pause of 0.5 seconds...",
                               endpoint)    
    pause = heat_globals.get('pause', 0.5)

    if not heat_globals.get('stack_delay'):
        msg_format.general_msg(f"The {endpoint} var 'stack_delay' is unset. Using default stack delay of 30 seconds...",
                               endpoint)    
    stack_delay = heat_globals.get('stack_delay', 30)

    amount = heat_globals['amount'] if 'amount' in heat_globals else globals_dict.get(
        'amount', 1
    )
    stack_name = heat_globals.get(
        'stack_name', globals_dict['organization']
    )
    
    stack_names = generate.generate_names(amount,
                                          stack_name)
    updated_heat_params = generate.update_heat_params(heat_globals,
                                                      heat_params,
                                                      endpoint,
                                                      debug)

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

    msg_format.success_msg(f"Provisioning {endpoint} Complete",
                           endpoint)
