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

    heat_file = heat_globals['heat_file']
    pause = heat_globals.get('pause', 0)
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
                          True,
                          debug)

        if update:
            stack.update()
        elif create:
            stack.create()
        else:
            stack.delete()

        if pause > 0 and stack_name != stack_names[-1]:
            msg_format.general_msg(f"Pausing for {pause} seconds...",
                                   endpoint)
            sleep(pause)

    msg_format.success_msg(f"Provisioning {endpoint} Complete",
                           endpoint)
