import os
from yaml import safe_load
from openstack import config, connect, enable_logging
from munch import Munch
from colorama import Fore
import time
from halo import Halo


def error_msg(error):
    print(Fore.RED + "ERROR:  " + Fore.RESET + error)


def info_msg(text):
    print(Fore.BLUE + "INFO:  " + Fore.RESET + text)


def success_msg(text):
    print(Fore.GREEN + "SUCCESS:  " + Fore.RESET + text)


def load_template(template):
    """Load Template"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


def create_container(container_name):
    """Create new object store container"""
    try:
        conn.object_store.create_container(name=container_name)
        print(f"Openstack_Swift:  Container {container_name} has been created"
              " in the object store")
        conn.set_container_access(name=container_name, access="public")
    except Exception as e:
        error_msg(f"Cannot create container, {container_name} it already exists\n ({e})")


def delete_container(container_name):
    """Delete container from object store"""
    try:
        if search_containers(container_name):
            conn.delete_container(container_name)
            success_msg(f"{container_name} container has been deleted from the object store")
        else:
            error_msg(f"Cannot delete container {container_name}, it doesn't exist")
    except:
        error_msg(f"An error occurred while deleting the {container_name} container")


def upload_objs(conn, container_name, dir):
    """Upload files and folders from a given directory to a cloud storage container"""
    try:
        for root, dirs, files in os.walk(dir):          

            # Create directory markers for all sub-directories
            [conn.create_directory_marker_object(container_name, d) for d in dirs]

            # Create objects for all files
            for file in files:
                file_path = os.path.join(root, file)
                conn.create_object(container_name, file_path)
                success_msg(f"{file_path} has been uploaded to the {container_name} container.")

        # Print a success message for the overall operation
        success_msg(f"All objects in the {dir} directory have been uploaded to the {container_name} container.")
    except Exception as e:
        error_msg(f"Failed to upload objects. {e}")


def delete_objs(conn, container_name):
    """Delete objects from a cloud storage container"""
    try:
        # List the objects in the container
        objects = conn.list_objects(container_name)

        # Delete each object
        for obj in objects:
            conn.delete_object(container_name, obj.name)
            success_msg(f"{obj.name} has been deleted from the {container_name} container.")

        # Print a success message for the overall operation
        success_msg(f"All objects in the {container_name} container have been deleted.")

    except Exception as e:
        error_msg(f"Failed to delete objects from the {container_name} container. {e}")


@Halo(text='Searching for container', spinner='bouncingBall')
def search_containers(container_name):
    """Search if container exists"""
    container_exists = conn.search_containers(name=container_name)
    return(container_exists)


def main():
    start = time.time()
    # Check create_all boolean logic in globals
    try:
        if global_params.globals['create_all']:
            global_params.swift.update({"action":"create"})
            print("create")
        if global_params.globals['create_all'] == "False":
            global_params.swift.update({"action":"delete"})
            print("delete")
        else:
            info_msg("Global create_all parameter not set. Moving on to Swift specific params... \n")

        # Check swift specific parameters in globals
        if global_params.swift['action'] == "create":
            create_container(orch_params.container_name['default'])
            upload_objs(conn, orch_params.container_name['default'], global_params.swift['asset_dir'])
        elif global_params.swift['action'] == "delete":
            delete_objs(conn, orch_params.container_name['default'])
            delete_container(orch_params.container_name['default'])
        elif global_params.swift['action'] == "update":
            upload_objs(orch_params.container_name['default'], global_params.swift['asset_dir'])
        else:
            info_msg("Parameters were not set for Swift container creation \n")

    except Exception as e:
        error_msg(e)

    end = time.time()
    print(end - start)

if __name__ == '__main__':
    print("*** Begin Object Storage Provisioning ***\n")
    config = config.loader.OpenStackConfig()
    global_params = Munch(load_template("globals.yaml"))
    orch = load_template(f"{global_params.heat['template_dir']}/main.yaml")
    orch_params = Munch(orch.get('parameters'))
    orch_params.container_name.update({'container_name':
                    orch_params.container_name['default']})
    conn = connect(cloud=global_params.globals['cloud'])
    main()
    print("\n*** End Object Storage Provisioning ***\n")
