"""
Swift Classes
"""
from time import sleep
from os import path, walk
from openstack.connection import Connection
from utils import msg_format


class SwiftContainer:
    """
    Swift Container Object for OpenStack

    Args:
        conn (Connection): OpenStack Connection
        name (str): Container name
        assets_dir (str): Directory containing assets
        delay (float): Delay between each action in seconds
        debug (bool): Debug flag
    """

    def __init__(self,
                 conn: Connection,
                 name: str,
                 assets_dir: str,
                 delay: float = 0,
                 debug: bool = False):

        self.conn = conn
        self.name = name
        self.assets_dir = assets_dir
        self.delay = delay
        self.debug = debug
        self.container = None

        self._search()

    def __hash__(self):
        """
        Hash function for the SwiftContainer object
        """
        return hash(
            tuple(sorted(vars(self)))
        )

    def __eq__(self, other):
        """
        Equality function for the SwiftContainer object
        """
        if not isinstance(other, self.__class__):
            return False

        return vars(self) == vars(other)

    def __str__(self):
        """
        String function for the SwiftContainer object
        """
        class_name = type(self).__name__
        output = f'{class_name}(\n'
        for key, value in self.__dict__.items():
            output += f'{key}: {value}\n'
        output += ')'
        return output

    def __repr__(self):
        """
        Representation function for the SwiftContainer object
        """
        return self.__str__()

    def create(self):
        """
        Creates the swift container and assets if they don't exist
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
        sleep(self.delay)

        if not container:
            msg_format.error_msg(f"Failed to create container '{name}'.",
                                 endpoint)
            return None

        self._set_access()
        self._upload_objects()

        self.container = container
        msg_format.success_msg(f"Created container '{name}'",
                               endpoint)
        msg_format.info_msg(container,
                            endpoint,
                            debug)

        return container

    def delete(self):
        """
        Deletes the swift container and assets if they exist
        """

        conn = self.conn
        name = self.name
        endpoint = 'Swift'

        if not self.container:
            msg_format.error_msg(f"Can't delete container. '{name}' dosn't exist.",
                                 endpoint)
            return None

        deleted = self._delete_objects()

        if not deleted:
            msg_format.error_msg(f"Could not delete all objects in container '{name}'",
                                 endpoint)
            return None

        msg_format.general_msg(f"Deleting container '{name}'",
                               endpoint)

        conn.object_store.delete_container(container=name)

        self.container = None
        msg_format.success_msg(f"Deleted container '{name}'",
                               endpoint)

        return None

    def update(self):
        """
        Updates the swift container and assets if they exist
        """

        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        if not self.container:
            msg_format.error_msg(f"Can't update container. '{name}' dosn't exist.",
                                 endpoint)
            return None

        deleted = self._delete_objects()

        if not deleted:
            msg_format.error_msg(f"Could not delete all objects in container '{name}'",
                                 endpoint)
            return None

        container = self._set_access()

        if not container:
            msg_format.error_msg(f"Failed to set access for container '{name}'",
                                 endpoint)
            return None

        self._upload_objects()

        msg_format.success_msg(f"Updated container '{name}'.",
                               endpoint)
        msg_format.info_msg(container,
                            endpoint,
                            debug)

        return container

    def _search(self):
        """
        Search for the swift container in OpenStack
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        msg_format.general_msg(f"Searching for container '{name}'...",
                               endpoint)

        result = conn.search_containers(name=name)
        sleep(self.delay)

        if result:
            first_container = result[0]
            self.container = first_container

            msg_format.general_msg(f"Found container '{name}'",
                                   endpoint)
            msg_format.info_msg(first_container,
                                endpoint,
                                debug)
            return True

        self.container = None
        msg_format.general_msg(f"Didn't find container '{name}'",
                               endpoint)
        return False

    def _set_access(self,
                    access: str = "public") -> object | None:
        """
        Set the swift container access.
        Can be 'public' or 'private'. Default is public.
        """

        conn = self.conn
        name = self.name
        endpoint = 'Swift'

        msg_format.general_msg(f"Setting container '{name}' to public",
                               endpoint)

        container = conn.set_container_access(name=name,
                                              access=access)
        sleep(self.delay)

        if not container:
            msg_format.error_msg(f"Failed to set {access} for container '{name}'",
                                 endpoint)
            return None

        msg_format.success_msg(f"Container '{name}' is now {access}",
                               endpoint)

        return container

    def _upload_objects(self) -> None:
        """
        Upload assets to the swift container
        """

        conn = self.conn
        name = self.name
        assets_dir = self.assets_dir
        endpoint = 'Swift'

        msg_format.general_msg(f"Uploading objects from '{assets_dir}' to container '{name}'",
                               endpoint)
        # Collect all the files and folders in the given directory
        files = []
        directories = []
        for (_dir, _ds, _fs) in walk(assets_dir):
            if not _ds + _fs:
                directories.append(_dir)
            else:
                files.extend([path.join(_dir, _f) for _f in _fs])

        for directory in directories:
            conn.create_directory_marker_object(container=name,
                                                name=directory)
            sleep(self.delay)

            msg_format.general_msg(f"Created directory marker '{directory}' in '{name}'.",
                                   endpoint)

        msg_format.success_msg(f"Directories created in '{name}'.",
                               endpoint)

        for file in files:
            file = file.replace('\\', '/')
            conn.create_object(container=name,
                               name=file,
                               filename=file)
            sleep(self.delay)

            msg_format.general_msg(f"Uploaded object '{file}' to '{name}'.",
                                   endpoint)

        msg_format.success_msg(f"Objects uploaded to '{name}'.",
                               endpoint)

        return None

    def _delete_objects(self) -> bool:
        """
        Delete assets from the swift container
        """

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Swift'

        swift_objects = self._list_objects()

        if not swift_objects:
            msg_format.general_msg(f"No objects found in container '{name}'",
                                   endpoint)
            return True

        msg_format.general_msg(f"Deleting objects from container '{name}'",
                               endpoint)

        for swift_object in swift_objects:
            object_name = str(swift_object.name)
            deleted = conn.delete_object(name,
                                         object_name)
            sleep(self.delay)

            if deleted:
                msg_format.general_msg(f"Deleted object '{object_name}' from '{name}'.",
                                       endpoint)
            else:
                msg_format.error_msg(f"Failed to delete object '{object_name}' from '{name}'.",
                                     endpoint)
                return False

        msg_format.success_msg(f"Objects have been deleted from '{name}'",
                               endpoint)
        msg_format.info_msg(swift_objects,
                            endpoint,
                            debug)

        return True

    def _list_objects(self) -> list | None:
        """
        List the objects in the swift container
        """

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
        sleep(self.delay)

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
