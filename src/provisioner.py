import json
import logging
import provision.heat as heat
import provision.swift as swift
import provision.guac as guac
import sys
import time
from guacamole import session
from openstack import connect, enable_logging
from utils.msg_format import error_msg, info_msg, success_msg, general_msg
from utils.load_template import load_global, load_heat, load_sec, load_env, load_template
from utils.manage_ids import update_ids, update_env


def main():
    try:
        start = time.time()

        # Create dictionaries for parsing
        global_dict = load_global()
        globals = global_dict.globals
        guacamole_globals = global_dict.guacamole
        heat_globals = global_dict.heat
        swift_globals = global_dict.swift
        heat_params = load_heat(global_dict.heat['template_dir']).parameters
        sec_params = load_sec(global_dict.heat['template_dir']).parameters
        env_params = load_env(global_dict.heat['template_dir']).parameters
        openstack_clouds = load_template('clouds.yaml')[
            'clouds'][f"{globals['cloud']}"]
        guacamole_clouds = load_template('clouds.yaml')['clouds']['guac']

        debug = globals['debug']

        # Enable debug logging if specified within the globals file
        enable_logging(globals['debug'])
        if debug:
            logging.getLogger("openstack").setLevel(logging.INFO)
            logging.getLogger("keystoneauth").setLevel(logging.INFO)
        else:
            logging.getLogger("openstack").setLevel(logging.CRITICAL)
            logging.getLogger("keystoneauth").setLevel(logging.CRITICAL)

        info_msg(json.dumps(global_dict, indent=4), debug)
        info_msg(json.dumps(heat_params, indent=4), debug)
        info_msg(json.dumps(sec_params, indent=4), debug)
        info_msg(json.dumps(env_params, indent=4), debug)

        general_msg("Connecting to OpenStack...")
        general_msg(f"Endpoint: {openstack_clouds['auth']['auth_url']}")
        general_msg(f"Project: {openstack_clouds['auth']['project_name']}")
        openstack_connect = connect(cloud=globals['cloud'])
        if openstack_connect:
            success_msg("Connected to OpenStack")
        # openstack_connect.

        general_msg("Connecting to Guacamole...")
        general_msg(f"Endpoint: {guacamole_globals['guac_host']}")
        guacamole_connect = session(
            guacamole_globals['guac_host'], 'mysql',
            guacamole_clouds['user'], guacamole_clouds['password'])
        if guacamole_connect:
            success_msg("Connected to Guacamole")
        # guacamole_connect.

        arg = sys.argv[1:]

        if len(arg) == 0:
            info_msg(
                "No arguments provided, please provide: "
                "'swift', 'heat', or 'guacamole' as an argument."
            )
        elif arg[0] == "swift":
            swift.provision(openstack_connect, globals, swift_globals, debug)
        elif arg[0] == "heat":
            update_env(openstack_connect, global_dict, True, debug)
            heat_params, sec_params, env_params = update_ids(
            openstack_connect, [heat_params, sec_params, env_params], [], False, debug)
            
            heat.provision(openstack_connect, globals, heat_globals,
                           heat_params, sec_params, debug)
        elif arg[0] == "guacamole":
            guac.provision(openstack_connect, guacamole_connect, globals, guacamole_globals,
                           heat_params, debug)
        elif arg[0] == "full":
            swift.provision(openstack_connect, globals, swift_globals, debug)

            update_env(openstack_connect, global_dict, True, debug)
            heat_params, sec_params, env_params = update_ids(
            openstack_connect, [heat_params, sec_params, env_params], [], False, debug)

            heat.provision(openstack_connect, globals, heat_globals,
                           heat_params, sec_params, debug)
            guac.provision(openstack_connect, guacamole_connect, globals, guacamole_globals,
                           heat_params, debug)

        end = time.time()
        general_msg("Total time: {:.2f} seconds".format(end - start))
    except Exception as e:
        error_msg(e)


if __name__ == '__main__':
    main()
