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

        globals_vars = load_template.load_yaml_file("globals.yaml")
        globals_dict: Dict[str, Any] = globals_vars['globals']
        swift_globals: Dict[str, Any] = globals_vars['swift']
        heat_globals: Dict[str, Any] = globals_vars['heat']
        guacamole_globals: Dict[str, Any] = globals_vars['guacamole']
        template_dir = heat_globals['template_dir']
        user_dir = guacamole_globals['user_dir']
        debug: bool = globals_dict['debug']

        heat_params = load_template.load_yaml_file("main.yaml", template_dir, debug).get('parameters')
        sec_params = load_template.load_yaml_file("sec.yaml", template_dir, debug).get('parameters')
        env_params = load_template.load_yaml_file("env.yaml", template_dir, debug).get('parameters')
        conn_params = load_template.load_yaml_file("guac.yaml", user_dir, debug)

        msg_format.info_msg(json.dumps(globals_vars, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(conn_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(heat_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(sec_params, indent=4), endpoint, debug)
        msg_format.info_msg(json.dumps(env_params, indent=4), endpoint, debug)

        clouds = load_template.load_template(
            'clouds.yaml', debug
        )['clouds']

        # Backwards compatibility
        if not heat_globals.get('cloud'):
            heat_globals['cloud'] = globals_dict['cloud']
        if not guacamole_globals.get('cloud'):
            guacamole_globals['cloud'] = 'guac'

        try:
            openstack_clouds: Dict[str, Any] = clouds[f"{heat_globals['cloud']}"]
        except KeyError:
            msg_format.error_msg(f"Cloud '{heat_globals['cloud']}' not found in clouds.yaml",
                                 endpoint)
            sys.exit(1)

        openstack_connect = connections.openstack_connection(heat_globals['cloud'],
                                                             openstack_clouds,
                                                             debug)

        if arg[0] == "swift":
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug)
        elif arg[0] == "heat":
            if env_params:
                manage_ids.update_env(openstack_connect,
                                      globals_dict,
                                      True,
                                      debug)
                heat_params, sec_params, env_params = manage_ids.update_ids(openstack_connect,
                                                                            [heat_params, sec_params, env_params],
                                                                            [],
                                                                            False,
                                                                            debug)
            heat.provision(openstack_connect,
                           globals_dict, heat_globals,
                           heat_params,
                           sec_params,
                           debug)
        elif arg[0] == "guacamole":
            try:
                guacamole_clouds: Dict[str, Any] = clouds[f"{guacamole_globals['cloud']}"]
            except KeyError:
                msg_format.error_msg(f"Cloud '{guacamole_globals['cloud']}' not found in clouds.yaml",
                                    endpoint)
                sys.exit(1)

            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           conn_params,
                           debug)
        elif arg[0] == "full":
            try:
                guacamole_clouds: Dict[str, Any] = clouds[f"{guacamole_globals['cloud']}"]
            except KeyError:
                msg_format.error_msg(f"Cloud '{guacamole_globals['cloud']}' not found in clouds.yaml",
                                    endpoint)
                sys.exit(1)

            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug)
            if env_params:
                manage_ids.update_env(openstack_connect,
                                      globals_dict,
                                      True,
                                      debug)
                heat_params, sec_params, env_params = manage_ids.update_ids(openstack_connect,
                                                                            [heat_params, sec_params, env_params],
                                                                            [],
                                                                            False,
                                                                            debug)
            heat.provision(openstack_connect,
                           globals_dict,
                           heat_globals,
                           heat_params,
                           sec_params,
                           debug)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           conn_params,
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
