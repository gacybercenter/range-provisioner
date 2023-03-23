import time
from openstack import config, connect, enable_logging
from utils.msg_format import error_msg, info_msg, success_msg
from utils.load_template import load_template, load_global, load_heat, load_sec
from utils.cli_parser import parser
from utils.build_type import provision_type
from orchestration.heat import search_stack
# from object_store.swift import search_containers, create_container, delete_container, upload_objs, delete_objs

def main():
    start = time.time()

    # Create dictionaries for parsing
    global_dict = load_global()
    heat_params = load_heat().parameters
    

    # Establish cloud connection
    provision_type()

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
    print(end - start)


if __name__ == '__main__':
    #Create Dictionaries
    global_dict = load_global()
    #Establish Connection
    conn = connect(cloud=global_dict.globals['cloud'])
    main()