import logging
import guacamole
import sys
import json
import openstack
import constants
import munch
from openstack.config import loader
from os import walk
from os.path import join


# TODO: add support for arguments(i.e. host, username, password, file.rc, etc)
event_action = constants.EVENT_ACTION
event_user_total = constants.EVENT_USER_TOTAL
event_user_prefix = constants.EVENT_USER_PREFIX
event_user_connection = constants.EVENT_USER_CONNECTION
event_user_password = constants.EVENT_USER_PASSWORD
event_user_organization = ""

guac_connection_group = constants.GUAC_CONN_GROUP
guac_host = constants.GUAC_HOST
guac_datasource = constants.GUAC_DATASOURCE
guac_user = constants.GUAC_USER
guac_password = constants.GUAC_PASS

container_name = constants.CONTAINER_NAME
assets_dir = constants.ASSETS_DIR
swift_api_ep = constants.SWIFT_API_EP

conn = openstack.connect()
# openstack.enable_logging(debug=True)


def create_container(container_name):
    """Create new object container"""
    container = conn.object_store.create_container(name=container_name)
    print(f"Container {container_name} has been created in the object store")

def upload_objects(dir, container_name):
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


    print(f"{assets_dir} and files have been created on the object store")

def main():

    try:    
        container_list = conn.list_containers()
        container_munch = container_list[0]
        if container_munch.name == container_name:
            print(f"Container {container_name} already exists")
    except IndexError:
        create_container(container_name)
        upload_objects(assets_dir, container_name)
        pass

if __name__ == '__main__':
    main()
