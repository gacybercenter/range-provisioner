#!/usr/bin/env python3
"""
Range Provisioner

Provisioning and deprovisioning for swift, heat, and guacamole
"""



import sys
import time
import json
import traceback
from typing import Dict, Any
from provision import swift, heat, guac
from utils import connections, load_template, manage_ids, msg_format

def main() -> None:
    """
    The main function that handles the provisioning process based on command line arguments.

    Parameters:
    None

    Returns:
    None
    """
    endpoint = 'Pipeline'

    try:
        # Parse and validate command line arguments
        arg = sys.argv[1:]
        if len(arg) == 0:
            msg_format.error_msg("No arguments provided.",
                                 endpoint)
            msg_format.general_msg("Valid arguments: 'swift', 'heat', 'guacamole', or 'full'",
                                   endpoint)
            return

        if arg[0] not in ["swift", "heat", "guacamole", "full"]:
            msg_format.error_msg(f"'{arg[0]}' is an invalid arguement.",
                                 endpoint)
            msg_format.general_msg("Valid arguments: 'swift', 'heat', 'guacamole', or 'full'",
                                   endpoint)
            return

        start_time = time.time()

        global_dict = load_template.load_global()
        globals: Dict[str, Any] = global_dict['globals']
        debug: bool = globals['debug']
        swift_globals: Dict[str, Any] = global_dict['swift']
        heat_globals: Dict[str, Any] = global_dict['heat']
        guacamole_globals: Dict[str, Any] = global_dict['guacamole']
        heat_params: Dict[str, Any] = load_template.load_heat(
            heat_globals['template_dir'], debug
        ).get('parameters')
        sec_params: Dict[str, Any] = load_template.load_sec(
            heat_globals['template_dir'], debug
        ).get('parameters')
        env_params: Dict[str, Any] = load_template.load_env(
            heat_globals['template_dir'], debug
        ).get('parameters')
        user_params: Dict[str, Any] = load_template.load_users(
            heat_globals['template_dir'], debug
        ).get('parameters')

        try:
            openstack_clouds: Dict[str, Any] = load_template.load_template(
                'clouds.yaml', debug
            )['clouds'][f"{heat_globals['cloud']}"]
        except KeyError:
            msg_format.error_msg(f"Cloud '{heat_globals['cloud']}' not found in clouds.yaml",
                                 endpoint)
            sys.exit(1)
        try:
            guacamole_clouds: Dict[str, Any] = load_template.load_template(
                'clouds.yaml', debug
            )['clouds'][f"{guacamole_globals['cloud']}"]
        except KeyError:
            msg_format.error_msg(f"Cloud '{guacamole_globals['cloud']}' not found in clouds.yaml",
                                 endpoint)
            sys.exit(1)

        msg_format.info_msg(json.dumps(global_dict, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(heat_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(sec_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(env_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(user_params, indent=4), endpoint, debug)

        openstack_connect = connections.openstack_connection(heat_globals['cloud'],
                                                             openstack_clouds,
                                                             debug)

        if arg[0] == "swift":
            swift.provision(openstack_connect,
                            globals,
                            swift_globals,
                            debug)
        elif arg[0] == "heat":
            if env_params:
                manage_ids.update_env(openstack_connect,
                                      global_dict,
                                      True,
                                      debug)
                heat_params, sec_params, env_params = manage_ids.update_ids(openstack_connect,
                                                                            [heat_params, sec_params, env_params],
                                                                            [],
                                                                            False,
                                                                            debug)
            heat.provision(openstack_connect,
                           globals, heat_globals,
                           heat_params,
                           sec_params,
                           debug)
        elif arg[0] == "guacamole":
            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals,
                           guacamole_globals,
                           heat_params,
                           user_params,
                           debug)
        elif arg[0] == "full":
            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
            swift.provision(openstack_connect,
                            globals,
                            swift_globals,
                            debug)
            if env_params:
                manage_ids.update_env(openstack_connect,
                                      global_dict,
                                      True,
                                      debug)
                heat_params, sec_params, env_params = manage_ids.update_ids(openstack_connect,
                                                                            [heat_params, sec_params, env_params],
                                                                            [],
                                                                            False,
                                                                            debug)
            heat.provision(openstack_connect,
                           globals,
                           heat_globals,
                           heat_params,
                           sec_params,
                           debug)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals,
                           guacamole_globals,
                           heat_params,
                           user_params,
                           debug)

        end_time = time.time()
        msg_format.general_msg(f"Total time: {end_time - start_time:.2f} seconds",
                               endpoint)

    except Exception as error:
        msg_format.error_msg(f"Error: {error}.\n\n {traceback.format_exc()}",
                             endpoint)
        sys.exit(1)

    msg_format.success_msg("Provisioning complete.",
                           endpoint)
    sys.exit(0)


if __name__ == '__main__':
    main()
