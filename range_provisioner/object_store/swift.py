from openstack import connect
from utils.msg_format import error_msg, info_msg, success_msg
from utils.load_template import load_template, load_global, load_heat


global_dict = load_global()
global_swift_dict = global_dict.swift
global_heat_dict = global_dict.heat
global_guac_dict = global_dict.guacamole
heat_dict = load_heat()
conn = connect(cloud=global_dict.globals['cloud'])


class SwiftProvision:
    def __init__(self, parsed_args):
        if parsed_args.pipeline:
            self.container_name = global_swift_dict['container_name']
        if parsed_args.pipeline is False:
            self.container_name = parsed_args.container_name
        
        print(self.container_name)


    def search_containers(self):
        """Search if container exists"""
        info_msg(f"Searching for {self.container_name} container...")
        container_exists = conn.search_containers(name=self.container_name)
        return(container_exists)


    def create_container(self):
        """Create new object store container"""
        try:
            container_created = conn.object_store.create_container(name=self.container_name)
            success_msg(f"Container {self.container_name} has been created"
                " in the object store")
            conn.set_container_access(name=self.container_name, access="public")
        except Exception as e:
            error_msg(f"Cannot create container, {self.container_name} it already exists \n ({e})")
            container_created = None
        return container_created


    def delete_container(self):
        """Delete container from object store"""
        container = SwiftProvision.search_containers(self)
        if container:
            conn.delete_container(self.container_name)
            success_msg(f"{self.container_name} container has been deleted from the object store")
        else:
            error_msg(f"Cannot delete container {self.container_name}, doesn't exist")


def swift_provision(parsed_args):
        if parsed_args.pipeline:
            global_swift_dict.update({'container_name': heat_dict.parameters['container_name']['default']})
            SwiftProvision(global_swift_dict['container_name'], parsed_args).create_container()
        if parsed_args.pipeline is False:
            SwiftProvision(global_swift_dict['container_name'], parsed_args).create_container()










# def upload_objs(container_name, dir):
#     """Create directory markers and upload objects"""
#     # Collect all the files and folders in the given directory
#     objs = []
#     dir_markers = []
#     for (_dir, _ds, _fs) in walk(dir):
#         if not (_ds + _fs):
#             dir_markers.append(_dir)
#         else:
#             objs.extend([path.join(_dir, _f) for _f in _fs])

#     # Create directory markers for folder structure
#     dir_markers = [
#         conn.create_directory_marker_object(
#             container_name,d,) for d in dir_markers
#         ]

#     # Create objects
#     objs = [
#         conn.create_object(
#         container_name, o,) for o in objs
#         ]

#     objects = conn.list_objects(container_name)

#     print("Openstack_Swift:  The following objects have been uploaded to the"
#           f" container {container_name}:")
#     for obj in objects:
#         print(f"  - {obj.name}")


# def delete_objs(container_name):
#     """Delete container objects"""
#     try:
#         objects = conn.list_objects(container_name)
#         print("Openstack_Swift:  The following objects were deleted from the"
#               f" {container_name} container:")
#         for obj in objects:
#             conn.delete_object(container_name, str(obj.name))
#             print(f"  - {obj.name}")
#     except Exception as e:
#         print(f"Openstack_Swift ERROR:  Cannot delete container objects"
#               f" in {container_name} the container doesn't exist")
#         print(f"Openstack_Swift ERROR:  {e}")



