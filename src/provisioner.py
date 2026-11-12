#!/usr/bin/env python3
"""
Range Provisioner

Provisioning and deprovisioning for swift, heat, and guacamole
"""


import sys
import time
import traceback
import argparse
from typing import Dict, Any
from provision import heat, swift, guac
from utils import connections, load_template, msg_format


def main() -> None:
    """
    The main function that handles the provisioning process based on command line arguments.

    Parameters:
    None

    Returns:
    None
    """

    start_time = time.time()
    endpoint = 'Pipeline'

    try:
        msg_format.general_msg("Starting Range Provisioner...", endpoint)    
        parser = argparse.ArgumentParser(description='Range Provisioner CLI')
        parser.add_argument('--action', help="Provision argument: swift, heat, guacamole, or full", action='store_true')
        parser.add_argument('--debug', help="Enable debug mode", action='store_true')
        args = parser.parse_args()
        arg = args.action
        
        if not arg:
            raise ValueError("No --action provided. Valid arguments: 'swift', 'heat', 'guacamole', or 'full'")
        if arg not in ['swift', 'heat', 'guacamole', 'full']:
            raise ValueError("Invalid argument. Valid arguments: 'swift', 'heat', 'guacamole', or 'full'")

        globals_vars = load_template.load_template("globals.yaml")
        globals_dict: Dict[str, Any] = globals_vars['globals']
        swift_globals: Dict[str, Any] = globals_vars['swift']
        heat_globals: Dict[str, Any] = globals_vars['heat']
        guacamole_globals: Dict[str, Any] = globals_vars['guacamole']

        debug: bool = args.debug or globals_dict['debug']
        heat_file = heat_globals.get('heat_file')
        guac_file = guacamole_globals.get('guac_file')

        # Backwards Compatibility
        if not heat_file:
            heat_file = heat_globals['template_dir'] + '/main.yaml'
            heat_globals['heat_file'] = heat_file
        if not guac_file:
            guac_file = guacamole_globals['user_dir'] + '/guac.yaml'
            guacamole_globals['guac_file'] = guac_file

        clouds = load_template.load_template('clouds.yaml')['clouds']

        try:
            openstack_clouds = clouds[heat_globals['cloud']]
        except KeyError as err:
            raise KeyError(
                f"Cloud '{heat_globals['cloud']}' not found in clouds.yaml") from err

        openstack_connect = connections.openstack_connection(heat_globals['cloud'],
                                                             openstack_clouds,
                                                             debug)

        if arg in ["full", "guacamole"]:
            try:
                guacamole_clouds = clouds[guacamole_globals['cloud']]
            except KeyError as err:
                raise KeyError(
                    f"Cloud '{guacamole_globals['cloud']}' not found in clouds.yaml") from err
            guacamole_connect = connections.guacamole_connection(guacamole_globals['cloud'],
                                                                 guacamole_clouds,
                                                                 debug)
        else:
            guacamole_connect = None

        if arg == "swift":
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug)
        elif arg == "heat":
            heat.provision(openstack_connect,
                           globals_dict,
                           heat_globals,
                           debug)
        elif arg == "guacamole":
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           debug)
        elif arg == "full":
            swift.provision(openstack_connect,
                            globals_dict,
                            swift_globals,
                            debug)
            heat.provision(openstack_connect,
                           globals_dict,
                           heat_globals,
                           debug)
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals_dict,
                           guacamole_globals,
                           debug)

    except Exception as error:
        msg_format.error_msg(f"{error}\n\n {traceback.format_exc()}",
                             endpoint)
        sys.exit(1)

    msg_format.success_msg("Provisioning complete.",
                           endpoint)

    end_time = time.time()
    msg_format.general_msg(f"Total time: {end_time - start_time:.2f} seconds",
                           endpoint)

    sys.exit(0)


if __name__ == '__main__':
    main()
