from openstack import connect
from utils.load_template import load_template, load_global, load_heat, load_sec
from utils.cli_parser import parser
from utils.msg_format import error_msg, info_msg, success_msg
from object_store.swift import swift_provision


# global_dict = load_global()
# global_swift_dict = global_dict.swift
# global_heat_dict = global_dict.heat
# global_guac_dict = global_dict.guacamole
# heat_dict = load_heat()


def provision_type():
    parsed_args = parser()
    if parsed_args.pipeline:
        # global_swift_dict.update({'container_name': heat_dict.parameters['container_name']['default']})
        Provision(parsed_args).pipeline()
    elif parsed_args.pipeline is False:
        # global_swift_dict.update({'container_name': parsed_args.container_name})
        Provision(parsed_args).cli()


class Provision:
    def __init__(self, parsed_args):
        self.parsed_args = parsed_args
        

    def pipeline(self):
        swift_provision(parsed_args=self.parsed_args)
        # heat_provision()
        # guac_provision()




    def cli(self):
        swift_provision(parsed_args=self.parsed_args)



        # if self.global_create_all:
        #     swift_provision(container_name, action="create")
        # elif self.global_create_all is False:
        #     swift_provision(container_name, action="delete")
        # else:
        #     if self.swift_create:
        #         swift_provision(container_name, action=self.swift_create)
        #     if self.swift_create is False:
        #         swift_provision(container_name, action=self.swift_create)


        # if self.global_create_all:
        #     print(self.global_create_all)
        #     create_container()
        # elif self.global_create_all is False:
        #     delete_container()
        # elif self.swift_params_action == "create":
        # elif global_dict['globals']['create_all'] is False:
        #     delete_container()
        # elif swift_params['action'] == "create":
        #     create_container()
        # elif swift_params['action'] == "delete":
            # delete_container()



#     print(args)
#     create_container(container_name)
#     # if args.action == "create":
#         # print("create")
#     #     create_container(conn, container_name)
#     # elif args.action == "delete":
#     #     delete_container(conn, container_name)
