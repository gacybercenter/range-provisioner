import json
import logging
import orchestration.provision as provision
import sys
import time
from openstack import connect, enable_logging
from utils.msg_format import error_msg, info_msg, success_msg, general_msg
from utils.load_template import load_global, load_heat, load_sec

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

        debug = globals['debug']

        # Enable debug logging if specified within the globals file
        if debug:
            enable_logging(global_dict.globals['debug'])
            logging.getLogger("openstack").setLevel(logging.INFO)
            logging.getLogger("keystoneauth").setLevel(logging.INFO)
        else:
            logging.getLogger("openstack").setLevel(logging.CRITICAL)
            logging.getLogger("keystoneauth").setLevel(logging.CRITICAL)

        info_msg(json.dumps(global_dict, indent=4), debug)
        info_msg(json.dumps(heat_params, indent=4), debug)
        info_msg(json.dumps(sec_params, indent=4), debug)


        #Establish Connection
        conn = connect(cloud=globals['cloud'])

        arg = sys.argv[1:]

        if len(arg) == 0:
            info_msg("No arguments provided, please provide 'swift', 'heat' or 'guacamole' as an argument.")
        elif arg[0] == "swift":
            provision.object_store(conn, globals, swift_globals, debug)
        elif arg[0] == "heat":
            provision.range(conn, globals, heat_globals, heat_params, sec_params, debug)
        elif arg[0] == "guacamole":
            provision.guacamole(conn, globals, guacamole_globals, heat_params, sec_params, debug)
        elif arg[0] == "full":
            provision.object_store(conn, globals, swift_globals, debug)
            provision.range(conn, globals, heat_globals, heat_params, sec_params, debug)
            provision.guacamole(conn, globals, guacamole_globals, heat_params, sec_params, debug)

        end = time.time()
        general_msg("Total time: {:.2f} seconds".format(end - start))
    except Exception as e:
        error_msg(e)
if __name__ == '__main__':
    main()