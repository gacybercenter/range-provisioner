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
        error_msg(error)
        return


def deprovision(conn: object,
                container_name: str,
                debug=False) -> None:
    """Deprovision container and delete assets"""

    try:
        delete(conn,
               container_name,
               debug)
    except Exception as error:
        error_msg(error)
        return


def search(conn: object,
           container_name: str,
           debug=False) -> list | None:
    """Search if container exists"""

    general_msg(f"Swift:  Searching for '{container_name}' container...")
    result = conn.search_containers(name=container_name)

    if result:
        success_msg(f"Swift:  '{container_name}' container exists")
        info_msg(result, debug)
        return result
    general_msg(f"Swift:  '{container_name}' container doesn't exist")
    return


def create(conn: object,
           container_name: str,
           debug=False) -> object | None:
    """Create new object store container"""

    exists = search(conn,
                    container_name,
                    debug)
    if exists:
        error_msg("Swift:  Cannot create container. "
                  f"'{container_name}' it already exists")
        return None

    general_msg("Swift:  Creating container "
                f"'{container_name}' in the object store")
    container = conn.object_store.create_container(name=container_name)
    if not container:
        error_msg("Swift:  Failed to create container "
                    f"'{container_name}'")
        return None

    success_msg(f"Swift:  Container '{container_name}' has been created")
    access(conn,
            container_name,
            debug)
    return container


def delete(conn: object,
           container_name: str,
           debug=False) -> None:
    """Delete container from object store"""

    exists = search(conn,
                    container_name,
                    debug)
    if not exists:
        error_msg("Swift:  Cannot delete container. "
                    f"'{container_name}' does not exists")
        return

    delete_objs(conn,
                container_name,
                debug)
    general_msg(f"Swift:  Deleting container... '{container_name}'")
    conn.object_store.delete_container(container_name,
                                       debug)
    success_msg(f"Swift:  '{container_name}' container has been deleted")


def access(conn: object,
           container_name: str,
           debug=False) -> None:
    """Set container access to public"""

    container = search(conn,
                       container_name,
                       debug)
    if container:
        general_msg("Swift:  Setting container "
                    f"'{container_name}' to public")
        result = conn.set_container_access(name=container_name,
                                           access="public")
        if result:
            success_msg(f"Swift:  Container '{container_name}' is now public")
            info_msg(result, debug)
            return result


def upload_objs(conn: object,
                container_name: str,
                directory: str,
                debug=False) -> None:
    """Create directory markers and upload objects"""

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
    success_msg("Swift:  Required directories have been created "
                f"in the '{container_name}' container")

    # Create objects
    objs = [
        conn.create_object(container_name,
                           obj.replace('\\', '/'),
                           filename=obj)
        for obj in objs
    ]
    success_msg("Swift:  Objects have been uploaded "
                f"to the '{container_name}' container")

    objects = conn.list_objects(container_name)
    if objects:
        info_msg(f"Swift:  Listing objects from '{container_name}'", debug)
        info_msg(json.dumps(objects, indent=4), debug)
        for obj in objects:
            general_msg(f"Swift:  Uploaded '{obj.name}'")


def delete_objs(conn: object,
                container_name: str,
                debug=False) -> None:
    """Delete container objects"""

    objects = conn.list_objects(container_name)
    info_msg(json.dumps(objects, indent=4), debug)
    general_msg(f"Swift:  Deleting objects from '{container_name}'")
    if objects:
        for obj in objects:
            conn.delete_object(container_name,
                                str(obj.name))
            general_msg(f"Swift:  Deleted '{obj.name}'")
        success_msg("Swift:  Objects have been deleted "
                    f"from '{container_name}'")
