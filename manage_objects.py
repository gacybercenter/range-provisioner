import logging
import sys
import openstack
import constants
import munch
from openstack.config import loader
from os import walk
from os.path import join

cloud = constants.CLOUD

swift_action = constants.SWIFT_ACTION
container_name = constants.CONTAINER_NAME
assets_dir = constants.ASSETS_DIR

conn = openstack.connect(cloud=cloud)
# openstack.enable_logging(debug=True)


def create_container(container_name):
    """Create new object store container"""
    conn.object_store.create_container(name=container_name)
    print(f"Openstack_Swift:  Container {container_name} has been created in the object store")
    #Set container to public
    conn.set_container_access(name=container_name, access="public")

def upload_objs(dir, container_name):
    """Create directory markers and upload objects"""
    # Collect all the files and folders in the given directory
    objs = []
    dir_markers = []
    for (_dir, _ds, _fs) in walk(dir):
        if not (_ds + _fs):
            dir_markers.append(_dir)
        else:
            objs.extend([join(_dir, _f) for _f in _fs])

    # Create directory markers for folder structure
    dir_markers = [
        conn.create_directory_marker_object(
            container_name,
            d,
            ) for d in dir_markers
    ]

    # Create objects
    objs = [
        conn.create_object(
            container_name,
            o,
            data=o
            ) for o in objs
    ]

    objects = conn.list_objects(container_name)

    print(f"Openstack_Swift:  The following objects have been created in the object store:")
    for obj in objects:
        print(f"  - {obj.name}")  


def delete_objs(container_name):
    """delete container objects"""
    objects = conn.list_objects(container_name)
    print(f"Openstack_Swift:  The following objects were deleted from the {container_name} container:")
    for obj in objects:
        conn.delete_object(container_name, str(obj.name))
        print(f"  - {obj.name}")  
    conn.delete_container(container_name)
    print(f"Openstack_Swift:  {container_name} container has been deleted from the object store")


def main():

    if swift_action == "create":
        container_result = conn.search_containers(container_name)
        if container_result:
            container = container_result[0].name
            print(f"Openstack_Swift:  {container_name} already exists in the object store")
        else:
            create_container(container_name)
            upload_objs(assets_dir, container_name)
            conn.set_container_access(container_name, "public")

    elif swift_action == "delete":
        container_result = conn.search_containers(container_name)
        if not container_result:
            print(f"Openstack_Swift:  {container_name} doesn't exist in the object store")
        else:
            delete_objs(container_name)

    # elif swift_action == "update":
    #     update_objs(container_name)

if __name__ == '__main__':
    main()
