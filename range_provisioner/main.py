from os import walk, path
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
        print(Fore.RED + "Openstack_Swift ERROR:  Cannot create container"
              f" {container_name} it already exists")
        print(Fore.RED +f"Openstack_Swift ERROR:  {e}")


def delete_container(container_name):
    """Delete container from object store"""
    if search_containers(container_name):
        conn.delete_container(container_name)
        success_msg(f"{container_name} container has been deleted from the object store")
    else:
        error_msg(f"Cannot delete container {container_name}, it doesn't exist")


def upload_objs(container_name, dir):
    """Create directory markers and upload objects"""
    # Collect all the files and folders in the given directory
    objs = []
    dir_markers = []
    for (_dir, _ds, _fs) in walk(dir):
        if not (_ds + _fs):
            dir_markers.append(_dir)
        else:
            objs.extend([path.join(_dir, _f) for _f in _fs])

    # Create directory markers for folder structure
    dir_markers = [
        conn.create_directory_marker_object(
            container_name,d,) for d in dir_markers
        ]

    # Create objects
    objs = [
        conn.create_object(
        container_name, o,) for o in objs
        ]

    objects = conn.list_objects(container_name)

    success_msg(f"The following objects have been uploaded to the {container_name} container :")
    for obj in objects:
        print(f"  - {obj.name}")


def delete_objs(container_name):
    """Delete container objects"""
    try:
        objects = conn.list_objects(container_name)
        success_msg(f"The following objects were deleted from the"
              f" {container_name} container:")
        for obj in objects:
            conn.delete_object(container_name, str(obj.name))
            print(f"  - {obj.name}")
    except Exception as e:
        error_msg(f"Cannot delete container objects in {container_name}, the container doesn't exist")
        error_msg(e)

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
        elif global_params.swift['action'] == "delete":
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
