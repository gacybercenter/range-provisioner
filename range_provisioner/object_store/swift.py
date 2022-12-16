from openstack import config, connect
from utils.msg_format import error_msg, info_msg, success_msg
from utils.load_template import load_template, load_global, load_heat

global_dict = load_global()
heat_params = load_heat().parameters
swift_params = global_dict.swift
swift_params.update({'container_name': heat_params['container_name']['default']})
container_name = swift_params['container_name']
conn = connect(cloud=global_dict.globals['cloud'])


def search_containers():
    """Search if container exists"""
    print(f"Openstack_Swift:  Searching for {container_name} container...")
    container_exists = conn.search_containers(name=container_name)
    return(container_exists)

def create_container():
    """Create new object store container"""
    try:
        container_created = conn.object_store.create_container(name=container_name)
        success_msg(f"Container {container_name} has been created"
              " in the object store")
        conn.set_container_access(name=container_name, access="public")
    except Exception as e:
        error_msg(f"Cannot create container, {container_name} it already exists \n ({e})")
        container_created = None
    return container_created

def delete_container(container_name):
    """Delete container from object store"""
    if search_containers(container_name):
        conn.delete_container(container_name)
        print(f"Openstack_Swift:  {container_name} container has been deleted"
              " from the object store")
    else:
        print("Openstack_Swift ERROR:  Cannot delete container"
              f" {container_name} it doesn't exist")


# def create_container(container_name):
#     """Create new object store container"""
#     try:
#         conn.object_store.create_container(name=container_name)
#         print(f"Openstack_Swift:  Container {container_name} has been created"
#               " in the object store")
#         conn.set_container_access(name=container_name, access="public")
#     except Exception as e:
#         print("Openstack_Swift ERROR:  Cannot create container"
#               f" {container_name} it already exists")
#         print(f"Openstack_Swift ERROR:  {e}")





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



