import json
import orchestration.heat as heat
import orchestration.guacamole as guac
import orchestration.swift as swift
import time
from openstack import config, connect, enable_logging
from utils.msg_format import error_msg, info_msg, success_msg
from utils.load_template import load_template, load_global, load_heat, load_sec
from utils.cli_parser import parser
from utils.build_type import provision_type

def main():
    start = time.time()

    # Create dictionaries for parsing
    global_dict = load_global()
    heat_params = load_heat(global_dict.heat['template_dir']).parameters
    sec_params = load_sec(global_dict.heat['template_dir']).parameters

    debug = global_dict.globals['debug']

    # Enable debug logging if specified within the globals file
    if debug:
        enable_logging(global_dict.globals['debug'])
        info_msg(json.dumps(global_dict, indent=4))
        info_msg(json.dumps(heat_params, indent=4))
        info_msg(json.dumps(sec_params, indent=4))


    #Establish Connection
    conn = connect(cloud=global_dict.globals['cloud'])
    heat.search_stack(conn, global_dict.globals['range_name'])

    # Establish cloud connection
    # provision_type()

    # elif args.default == True:
    #     cli_provision(args)





        
    # Check create_all boolean logic in globals
    # try:
        # Check create_all boolean logic in clobals
        # try:
        #     if 


        # if global_params.globals['create_all']:
        #     global_params.swift.update({"action": "create"})
        #     print("create")
        # if global_params.globals['create_all'] == "False":
        #     global_params.swift.update({"action": "delete"})
        #     print("delete")
        # else:
        #     info_msg("Global create_all parameter not set. Moving on to Swift specific params... \n")

        # # Check swift specific parameters in globals
        # if global_params.swift['action'] == "create":
        #     create_container(container_name)
        #     upload_objs(conn, container_name, asset_dir)
        # elif global_params.swift['action'] == "delete":
        #     delete_objs(conn, container_name)
        #     delete_container(container_name)
        # elif global_params.swift['action'] == "update":
        #     upload_objs(container_name, asset_dir)
        # else:
        #     info_msg("Parameters were not set for Swift container creation \n")

    # except Exception as e:
    #     error_msg(e)

    end = time.time()
    info_msg("Total time: {:.2f} seconds".format(end - start))

if __name__ == '__main__':
    main()