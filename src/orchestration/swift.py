"""
Contains all the main functions for provisioning Swift
"""
import json
from os import path, walk
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn: object,
              container_name: str,
              asset_dir: str,
              debug=False) -> None:
    """Provision container and upload assets"""

    endpoint = 'Swift'

    general_msg("Provisioning Swift",
                endpoint)

    try:
        container = create(conn,
                           container_name,
                           debug)
        if container:
            upload_objs(conn,
                        container_name,
                        asset_dir,
                        debug)
        else:
            return

    except Exception as error:
        error_msg(error,
                  endpoint)
        return

    success_msg("Provisioned Swift",
                endpoint)


def deprovision(conn: object,
                container_name: str,
                debug=False) -> None:
    """Deprovision container and delete assets"""

    endpoint = 'Swift'

    general_msg("Deprovisioning Swift",
                endpoint)

    try:
        delete(conn,
               container_name,
               debug)

    except Exception as error:
        error_msg(error,
                  endpoint)
        return

    success_msg("Deprovisioned Swift",
                endpoint)


def search(conn: object,
           container_name: str,
           debug=False) -> list | None:
    """Search if container exists"""

    endpoint = 'Swift'

    general_msg(f"Searching for '{container_name}' container...",
                endpoint)
    result = conn.search_containers(name=container_name)

    if result:
        success_msg(f"'{container_name}' container exists",
                    endpoint)
        info_msg(result,
                 endpoint,
                 debug)
        return result
    general_msg(f"'{container_name}' container doesn't exist",
                endpoint)
    return


def create(conn: object,
           container_name: str,
           debug=False) -> object | None:
    """Create new object store container"""

    endpoint = 'Swift'

    exists = search(conn,
                    container_name,
                    debug)
    if exists:
        error_msg(f"Cannot create container. '{container_name}' already exists",
                  endpoint)
        return None

    general_msg(f"Creating container '{container_name}' in the object store",
                endpoint)
    container = conn.object_store.create_container(name=container_name)
    if not container:
        error_msg(f"Failed to create container '{container_name}'",
                  endpoint)
        return None

    success_msg(f"Container '{container_name}' has been created",
                endpoint)
    access(conn,
           container_name,
           debug)
    return container


def delete(conn: object,
           container_name: str,
           debug=False) -> None:
    """Delete container from object store"""

    endpoint = 'Swift'

    exists = search(conn,
                    container_name,
                    debug)
    if not exists:
        error_msg(f"Cannot delete container. '{container_name}' does not exists",
                  endpoint)
        return

    delete_objs(conn,
                container_name,
                debug)
    general_msg(f"Deleting container... '{container_name}'",
                endpoint)
    conn.object_store.delete_container(container_name,
                                       debug)
    success_msg(f"'{container_name}' container has been deleted",
                endpoint)


def access(conn: object,
           container_name: str,
           debug=False) -> None:
    """Set container access to public"""

    endpoint = 'Swift'

    container = search(conn,
                       container_name,
                       debug)
    if container:
        general_msg(f"Setting container '{container_name}' to public",
                    endpoint)
        result = conn.set_container_access(name=container_name,
                                           access="public")
        if result:
            success_msg(f"Container '{container_name}' is now public",
                        endpoint)
            info_msg(result,
                     endpoint,
                     debug)
            return result


def upload_objs(conn: object,
                container_name: str,
                directory: str,
                debug=False) -> None:
    """Create directory markers and upload objects"""

    endpoint = 'Swift'

    # Collect all the files and folders in the given directory
    objs = []
    dir_markers = []
    for (_dir, _ds, _fs) in walk(directory):
        if not _ds + _fs:
            dir_markers.append(_dir)
        else:
            objs.extend([path.join(_dir, _f) for _f in _fs])

    # Create directory markers for folder structure
    dir_markers = [
        conn.create_directory_marker_object(container_name,
                                            dir_mark)
        for dir_mark in dir_markers
    ]
    success_msg(f"Required directories created in the '{container_name}' container",
                endpoint)

    # Create objects
    objs = [
        conn.create_object(container_name,
                           obj.replace('\\', '/'),
                           filename=obj)
        for obj in objs
    ]
    success_msg(f"Objects uploaded to the '{container_name}' container",
                endpoint)

    objects = conn.list_objects(container_name)
    if objects:
        info_msg(f"Listing objects from '{container_name}'",
                 endpoint,
                 debug)
        info_msg(json.dumps(objects, indent=4),
                 endpoint,
                 debug)
        for obj in objects:
            general_msg(f"Uploaded '{obj.name}'",
                        endpoint)


def delete_objs(conn: object,
                container_name: str,
                debug=False) -> None:
    """Delete container objects"""

    endpoint = 'Swift'

    objects = conn.list_objects(container_name)
    info_msg(json.dumps(objects, indent=4),
             endpoint,
             debug)
    general_msg(f"Deleting objects from '{container_name}'",
                endpoint)
    if objects:
        for obj in objects:
            conn.delete_object(container_name,
                               str(obj.name))
            general_msg(f"Deleted '{obj.name}'",
                        endpoint)
        success_msg(f"Objects have been deleted from '{container_name}'",
                    endpoint)
