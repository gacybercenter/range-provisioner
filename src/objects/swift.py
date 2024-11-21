"""
Connection Classes
"""
from time import sleep
from os import path, walk
from typing import Dict, Any, List
from openstack.connection import Connection
from utils import msg_format


class SwiftContainer:
    """
    Connection Template Object for Guacamole

    Args:
        gconn: Specific type of Connection object
        name: Name of the connection
        protocol: Protocol of the connection
        identifier: Identifier of the connection
        debug: Debug mode
    """

    def __init__(self,
                 conn: Connection,
                 name: str,
                 assets_dir: str,
                 debug: bool = False):

        self.conn = conn
        self.name = name
        self.assets_dir = assets_dir
        self.debug = debug
        self.container = None
        self.objects = None

        self._search()

    def __hash__(self):
        return hash(
            tuple(sorted(vars(self)))
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return vars(self) == vars(other)

    def __str__(self):
        class_name = type(self).__name__
        output = f'{class_name}(\n'
        for key, value in self.__dict__.items():
            output += f'{key}: {value}\n'
        output += ')'
        return output

    def __repr__(self):
        return self.__str__()

    def create(self,
               delay: float = 0):
        """Create a new container with the provided parameters."""

        response = self._create_container()
        sleep(delay)

        return response

    def delete(self,
               delay: float = 0):
        """Delete a new container with the provided parameters."""

        response = self._delete_container()
        sleep(delay)

        return response

    def update(self,
               delay: float = 0):
        """Update a new container with the provided parameters."""

        response = self._update_container()
        sleep(delay)

        return response

    def _search(self):
        """Search for a container and return the container if it exists."""

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        msg_format.general_msg(f"Searching for container '{name}'...",
                               endpoint)
        result = conn.search_containers(name=name)
        if result:
            first_container = result[0]
            msg_format.general_msg(f"Found container '{name}'",
                                   endpoint)
            msg_format.info_msg(first_container,
                                endpoint,
                                debug)
            self.container = first_container
            return True

        msg_format.general_msg(f"Didn't find container '{name}'",
                               endpoint)
        self.container = None
        return False

    def _create_container(self):
        """
        Default implementation for creating a container
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        if self.container:
            msg_format.error_msg(f"Can't create container. '{name}' already exists.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Creating container '{name}'",
                               endpoint)

        container = conn.object_store.create_container(name=name)

        if not container:
            msg_format.error_msg(f"Failed to create container '{name}'.",
                                 endpoint)
            return None

        self.container = container
        self._set_access()
        self._upload_objects()

        msg_format.success_msg(f"Created container '{name}'",
                               endpoint)
        msg_format.info_msg(container,
                            endpoint,
                            debug)

        return container

    def _delete_container(self):
        """
        Default implementation for deleting a container
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        if not self.container:
            msg_format.error_msg(f"Can't delete container. '{name}' dosn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Deleting container '{name}'",
                               endpoint)

        deleted = self._delete_objects()

        if not deleted:
            msg_format.error_msg(f"Failed to delete container '{name}'",
                                 endpoint)
            return None

        conn.object_store.delete_container(name=name)

        self.container = None
        msg_format.success_msg(f"Deleted container '{name}'",
                               endpoint)

        return None

    def _update_container(self):
        """
        Default implementation for creating a container
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        if not self.container:
            msg_format.error_msg(f"Can't update container. '{name}' dosn't exist.",
                                 endpoint)
            return None

        self._delete_objects()
        self._set_access()
        self._upload_objects()

        container = conn.get_container(name=name)
        self.container = container

        if not container:
            msg_format.error_msg(f"Failed to update container '{name}'",
                                 endpoint)
            return None

        msg_format.success_msg(f"Updated container '{name}'.",
                               endpoint)
        msg_format.info_msg(container,
                            endpoint,
                            debug)

        return container

    def _set_access(self,
                    access: str = "public") -> object | None:
        """
        Set container access. Can be public or private. Default is public.
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        msg_format.general_msg(f"Setting container '{name}' to public",
                               endpoint)
        container = conn.set_container_access(name=name,
                                              access=access)
        if not container:
            msg_format.error_msg(f"Failed to set {access} for container '{name}'",
                                 endpoint)
            return None

        msg_format.general_msg(f"Container '{name}' is now {access}",
                               endpoint)
        msg_format.info_msg(container,
                            endpoint,
                            debug)

        self.container = container
        return container

    def _upload_objects(self) -> None:
        """Create directory markers and upload objects"""

        conn = self.conn
        name = self.name
        assets_dir = self.assets_dir
        debug = self.debug
        endpoint = 'Swift'

        # Collect all the files and folders in the given directory
        files = []
        dir_markers = []
        swift_objects = []
        for (_dir, _ds, _fs) in walk(assets_dir):
            if not _ds + _fs:
                dir_markers.append(_dir)
            else:
                files.extend([path.join(_dir, _f) for _f in _fs])

        for dir_mark in dir_markers:
            dir_marker = conn.create_directory_marker_object(container=name,
                                                             name=dir_mark)
            if dir_marker:
                dir_markers.append(dir_marker)
                msg_format.info_msg(dir_marker,
                                    endpoint,
                                    debug)
            else:
                msg_format.error_msg(f"Failed to create directory marker '{dir_mark}' in container '{name}'.",
                                     endpoint)

        msg_format.success_msg(f"Directories created in container '{name}'.",
                               endpoint)

        for file in files:
            file = file.replace('\\', '/')
            swift_object = conn.create_object(container=name,
                                              name=file,
                                              filename=file)
            if swift_object:
                swift_objects.append(swift_object)
                msg_format.general_msg(f"Uploaded object '{file}' to container '{name}'.",
                                       endpoint)
            else:
                msg_format.error_msg(f"Failed to upload object '{file}' to container '{name}'.",
                                     endpoint)

        msg_format.success_msg(f"Objects uploaded to container '{name}'.",
                               endpoint)
        msg_format.info_msg(swift_objects,
                            endpoint,
                            debug)

        self.objects = swift_objects
        return swift_objects

    def _delete_objects(self) -> bool:
        """Delete container objects"""

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        swift_objects = self._list_objects()

        if not swift_objects:
            msg_format.error_msg(f"No container objects found in '{name}'",
                                 endpoint)
            return False

        msg_format.general_msg(f"Deleting objects from '{name}'",
                               endpoint)

        for swift_object in swift_objects:
            object_name = str(swift_object.name)
            deleted = conn.delete_object(name,
                                         object_name)
            if deleted:
                msg_format.general_msg(f"Deleted object '{object_name}' from container '{name}'.",
                                       endpoint)
            else:
                msg_format.error_msg(f"Failed to delete object '{object_name}' from container '{name}'.",
                                     endpoint)
                return False

        msg_format.success_msg(f"Objects have been deleted from '{name}'",
                               endpoint)
        msg_format.info_msg(swift_objects,
                            endpoint,
                            debug)

        return True

    def _list_objects(self) -> List[object]:
        """List container objects"""

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        if not self.container:
            msg_format.error_msg(f"Can't list container. '{name}' dosn't exists.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Listing objects in container '{name}'",
                               endpoint)

        swift_objects = conn.list_objects(name)

        if not swift_objects:
            msg_format.general_msg(f"No container objects found in '{name}'",
                                   endpoint)
        else:
            msg_format.general_msg(f"Objects found in container '{name}'",
                                   endpoint)
        msg_format.info_msg(swift_objects,
                            endpoint,
                            debug)

        return swift_objects
