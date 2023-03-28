import json
from os import path, walk
from utils.msg_format import error_msg, info_msg, success_msg


def provision(conn, container_name, asset_dir, debug=False):
    """Provision container and upload assets"""
    try:
        container = create(conn, container_name, debug)
        if container:
            upload_objs(conn, container_name, asset_dir, debug)
        else:
            return None
    except Exception as e:
        error_msg(e)


def deprovision(conn, container_name, debug=False):
    """Deprovision container and delete assets"""
    try:
        delete(conn, container_name, debug)
    except Exception as e:
        error_msg(e)


def search(conn, container_name, debug=False):
    """Search if container exists"""
    try:
        info_msg(f"Searching for {container_name} container...")
        result = conn.search_containers(name=container_name)

        if result:
            success_msg(f"{container_name} container exists")
            return result
        info_msg(f"{container_name} container doesn't exist")
        return None
    except Exception as e:
        error_msg(e)


def create(conn, container_name, debug=False):
    """Create new object store container"""
    try:
        exists = search(conn, container_name, debug)
        if exists:
            error_msg(
                f"Cannot create container, {container_name} it already exists")
            return None
        else:
            info_msg(
                f"Creating container {container_name} in the object store", debug)
            container = conn.object_store.create_container(name=container_name)
            if container:
                success_msg(f"Container {container_name} has been created")
                return container
    except Exception as e:
        error_msg(e)


def delete(conn, container_name, debug=False):
    """Delete container from object store"""
    try:
        exists = search(conn, container_name, debug)
        if exists:

            delete_objs(conn, container_name, debug)

            info_msg(f"Deleting container... {container_name}", debug)
            conn.object_store.delete_container(container_name, debug)
            success_msg(f"{container_name} container has been deleted")
        else:
            error_msg(
                f"Cannot delete container, {container_name} does not exists")
            return None
    except Exception as e:
        error_msg(e)


def access(conn, container_name, debug=False):
    """Set container access to public"""
    try:
        container = search(conn, container_name, debug)
        if container:
            info_msg(f"Setting container {container_name} to public", debug)
            access = conn.set_container_access(
                name=container_name, access="public")
            if access:
                success_msg(f"Container {container_name} is now public")
                return access
    except Exception as e:
        error_msg(e)


def upload_objs(conn, container_name, dir, debug=False):
    """Create directory markers and upload objects"""
    try:
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
                container_name, d,) for d in dir_markers
        ]
        success_msg(
            f"Required directories have been created in the {container_name} container")

        # Create objects
        objs = [
            conn.create_object(
                container_name, o,) for o in objs
        ]
        success_msg(
            f"Objects have been uploaded to the {container_name} container")

        objects = conn.list_objects(container_name)
        if objects:
            info_msg(f"Listing objects from {container_name}", debug)
            info_msg(json.dumps(objects, indent=4), debug)
            for obj in objects:
                info_msg(f"uploaded:     {obj.name}", debug)
    except Exception as e:
        error_msg(e)


def delete_objs(conn, container_name, debug=False):
    """Delete container objects"""
    try:
        objects = conn.list_objects(container_name)
        info_msg(json.dumps(objects, indent=4), debug)
        info_msg(f"Deleting objects from {container_name}", debug)
        if objects:
            for obj in objects:
                conn.delete_object(container_name, str(obj.name))
                info_msg(f"Deleted:     {obj.name}", debug)
            success_msg(f"Objects have been deleted from {container_name}")
    except Exception as e:
        error_msg(e)
