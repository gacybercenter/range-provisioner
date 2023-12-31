#!/usr/bin/env python3
"""
Range Provisioner

Provisioning and deprovisioning for swift, heat, and guacamole
"""
import json
import logging
import traceback
import sys
import time
from guacamole import session
from openstack import connect, enable_logging
from provision import swift, heat, guac
from utils.msg_format import error_msg, info_msg, success_msg, general_msg
from utils.load_template import load_global, load_heat, load_sec, load_env, load_users, load_template
from utils.manage_ids import update_ids, update_env


def main():
    """
    This function is the main entry point of the program.
    It sets up the necessary dictionaries for parsing and connects to OpenStack and Guacamole.
    It then checks the command line arguments and executes the corresponding provisioning functions.
    Finally, it calculates and prints the total execution time of the program.

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
            error_msg(
                "No arguments provided.",
                endpoint
            )
            general_msg(
                "Valid arguments: 'swift', 'heat', 'guacamole', or 'full'",
                endpoint
            )
            return

        if arg[0] not in ["swift", "heat", "guacamole", "full"]:
            error_msg(
                f"'{arg[0]}' is an invalid arguement.",
                endpoint
            )
            general_msg(
                "Valid arguments: 'swift', 'heat', 'guacamole', or 'full'",
                endpoint
            )
            return

        start = time.time()

        # Create dictionaries for parsing
        global_dict = load_global()
        globals = global_dict['globals']
        debug = globals['debug']
        # if arg[1] == "--debug":
        #     debug = True
        guacamole_globals = global_dict['guacamole']
        heat_globals = global_dict['heat']
        swift_globals = global_dict['swift']
        heat_params = load_heat(global_dict['heat']['template_dir'],
                                debug).get('parameters')
        sec_params = load_sec(global_dict['heat']['template_dir'],
                              debug).get('parameters')
        env_params = load_env(global_dict['heat']['template_dir'],
                              debug).get('parameters')
        user_params = load_users(global_dict['heat']['template_dir'],
                                 debug).get('parameters')
        openstack_clouds = load_template('clouds.yaml',
                                         debug)['clouds'][f"{globals['cloud']}"]
        guacamole_clouds = load_template('clouds.yaml',
                                         debug)['clouds']['guac']

        # Enable debug logging if specified within the globals file
        enable_logging(globals['debug'])
        if debug:
            logging.getLogger("openstack").setLevel(logging.INFO)
            logging.getLogger("keystoneauth").setLevel(logging.INFO)
        else:
            logging.getLogger("openstack").setLevel(logging.CRITICAL)
            logging.getLogger("keystoneauth").setLevel(logging.CRITICAL)

        # Dump the dictionaries to the console
        info_msg(json.dumps(global_dict, indent=4),
                 endpoint,
                 debug)
        info_msg(json.dumps(heat_params, indent=4),
                 endpoint,
                 debug)
        info_msg(json.dumps(sec_params, indent=4),
                 endpoint,
                 debug)
        info_msg(json.dumps(env_params, indent=4),
                 endpoint,
                 debug)
        info_msg(json.dumps(user_params, indent=4),
                 endpoint,
                 debug)

        # Connect to OpenStack
        general_msg("Connecting to OpenStack...",
                    endpoint)
        info_msg(f"Endpoint: {openstack_clouds['auth']['auth_url']}",
                 endpoint,
                 debug)
        info_msg(f"Project: {openstack_clouds['auth']['project_name']}",
                 endpoint,
                 debug)
        openstack_connect = connect(cloud=globals['cloud'])
        if openstack_connect:
            success_msg("Connected to OpenStack",
                        endpoint)

        # Connect to Guacamole
        general_msg("Connecting to Guacamole...",
                    endpoint)
        info_msg(f"Endpoint: {guacamole_clouds['host']}",
                 endpoint,
                 debug)
        guacamole_connect = session(guacamole_clouds['host'],
                                    guacamole_clouds['data_source'],
                                    guacamole_clouds['username'],
                                    guacamole_clouds['password'])
        if guacamole_connect:
            success_msg("Connected to Guacamole",
                        endpoint)

        # Provision 'swift', 'heat', and or 'guacamole'
        if arg[0] == "swift":
            swift.provision(openstack_connect,
                            globals,
                            swift_globals,
                            debug)
        elif arg[0] == "heat":
            if env_params:
                update_env(openstack_connect,
                           global_dict,
                           True,
                           debug)
                (heat_params,
                 sec_params,
                 env_params) = update_ids(openstack_connect,
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
        elif arg[0] == "guacamole":
            guac.provision(openstack_connect,
                           guacamole_connect,
                           globals,
                           guacamole_globals,
                           heat_params,
                           user_params,
                           debug)
        elif arg[0] == "full":
            swift.provision(openstack_connect,
                            globals,
                            swift_globals,
                            debug)

            if env_params:
                update_env(openstack_connect,
                           global_dict,
                           True,
                           debug)
                (heat_params,
                 sec_params,
                 env_params) = update_ids(openstack_connect,
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

        end = time.time()
        general_msg(f"Total time: {end - start:.2f} seconds",
                    endpoint)

    except Exception as error:
        error_msg(f"Error: {error}.\nTraceback: {traceback.format_exc()}",
                  endpoint)

        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
