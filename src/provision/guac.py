"""
Guacamole provisioning script
Author: Marcus Corulli
Date: 5/1/2024
Version: 2.0

Description:
    Handles the logic for provisioning Guacamole
"""
from utils import msg_format, generate, load_template
from objects.users import NewUsers, CurrentUsers
from objects.connections import NewConnections, CurrentConnections


def provision(oconn: object,
              gconn: object,
              globals_dict: dict,
              guacamole_globals: dict,
              debug: bool):
    """
    Provisions or deprovisions Guacamole based on the given parameters.

    Args:
        oconn (object): The Heat connection object.
        gconn (object): The Guacamole connection object.
        globals_dict (dict): The globals dictionary.
        guacamole_globals (dict): The Guacamole globals dictionary.
        debug (bool): The debug flag.

    Returns:
        None
    """

    endpoint = 'Guacamole'

    create, update = generate.set_provisioning_flags(globals_dict.get('provision'),
                                                     guacamole_globals.get('provision'),
                                                     guacamole_globals.get('update'),
                                                     endpoint,
                                                     debug)

    if create is None:
        msg_format.general_msg(f"Skipping {endpoint} provisioning.", endpoint)
        return

    if not guacamole_globals.get('org_name'):
        organization = globals_dict.get('organization')
        msg_format.general_msg(f"The {endpoint} var 'org_name' is unset. Using global organization '{organization}'...",
                               endpoint)
        guacamole_globals['org_name'] = organization
    org_name = guacamole_globals['org_name']

    if not guacamole_globals.get('pause'):
        msg_format.general_msg(f"The {endpoint} var 'pause' is unset. Using default pause of 0.5 seconds...",
                               endpoint)    
    pause = guacamole_globals.get('pause', 0.5)

    if not guacamole_globals.get('guac_file'):
        msg_format.error_msg(f"The {endpoint} var 'guac_file' is unset. Create and Update wont work.",
                             endpoint)
    guac_file = guacamole_globals.get('guac_file')
    template_dir = globals_dict.get('template_dir')

    conn_params = load_template.load_yaml_file(guac_file,
                                                template_dir,
                                                debug)

    if not create:
        names = [
            group
            for group, data in conn_params['groups'].items()
            if data.get('parent') == 'ROOT'
        ]

        if not names:
            msg_format.error_msg("No connection groups specified in the config file.",
                                 "Guacamole")
            return

        current_connections = CurrentConnections(gconn,
                                                 'ROOT',
                                                 names,
                                                 debug)
        current_connections.delete(delay=pause)

        current_users = CurrentUsers(gconn,
                                     org_name,
                                     debug)
        current_users.delete(delay=pause)

    else:
        new_connections = NewConnections(gconn,
                                         oconn,
                                         conn_params,
                                         debug)

        if update:
            new_connections.update(delay=pause)
        else:
            new_connections.create(delay=pause)

        new_users = NewUsers(gconn,
                             conn_params,
                             org_name,
                             new_connections.connections,
                             debug)

        if update:
            new_users.update(delay=pause)
        else:
            new_users.create(delay=pause)

        msg_format.general_msg("User artifacts:",
                               endpoint)
        for user in new_users.users:
            msg_format.general_msg(f"Username: {user.username}, Password: {user.password}",
                                   endpoint)

    msg_format.success_msg(f"{endpoint} provisioning complete.",
                           endpoint)
