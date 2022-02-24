import guacamole
import tarfile
import os
import sys
import json
import openstack
import constants
from openstack.config import loader

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
source_dir = constants.ASSETS_DIR

conn = openstack.connect()

def create_container(container_name):
    """Create new object container"""
    container = conn.object_store.create_container(name=container_name)
    print(f"Container {container_name} has been created in the object store")

def check_container(container_name):
    """Check for existing object container"""
    for cont in conn.object_store.containers():
        dict_cont = dict(cont)
        if dict_cont['name'] is not container_name:
            print(f"Container with the name {container_name} already exists")
        return True

def make_tarfile(archive_name, source_dir):
    with tarfile.open(archive_name + '.tar.gz', mode='w:gz') as archive:
        archive.add(source_dir)

def upload_objects(container_name):

#Check and create container for object storage if it doesn't exist
if check_container(container_name) is None:
    create_container(container_name)

#Create gzip file from assets directory

make_tarfile("archive", source_dir)
