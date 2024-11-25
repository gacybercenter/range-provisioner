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
        debug (bool): Debug flag
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
        self.endpoint = 'Swift'
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

    def create(self,
               delay: float = 0):
        """
        Creates the swift container and assets if they don't exist
        """

        if self.container:
            msg_format.error_msg(f"Can't create container '{self.name}' because it already exists.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Creating container '{self.name}'...",
                               self.endpoint)

        container = self.conn.object_store.create_container(name=self.name)
        sleep(delay)

        if not container:
            msg_format.error_msg(f"Failed to create container '{self.name}'",
                                 self.endpoint)
            return None

        self._set_access(delay=delay)
        self._upload_objects(delay=delay)

        self.container = container
        msg_format.success_msg(f"Created container '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(container,
                            self.endpoint,
                            self.debug)

        return container

    def delete(self, delay: float = 0):
        """
        Deletes the swift container and assets if they exist
        """

        if not self.container:
            msg_format.error_msg(f"Can't delete container. '{self.name}' dosn't exist.",
                                 self.endpoint)
            return None

        deleted = self._delete_objects(delay=delay)

        if not deleted:
            msg_format.error_msg(f"Could not delete all objects in container '{self.name}'",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Deleting container '{self.name}'...",
                               self.endpoint)

        self.conn.object_store.delete_container(container=self.name)
        sleep(delay)

        self.container = None
        msg_format.success_msg(f"Deleted container '{self.name}'",
                               self.endpoint)

        return None

    def update(self, delay: float = 0):
        """
        Updates the swift container and assets if they exist
        """

        if not self.container:
            msg_format.error_msg(f"Can't update container. '{self.name}' dosn't exist.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Updating container '{self.name}'...",
                               self.endpoint)

        deleted = self._delete_objects(delay=delay)

        if not deleted:
            msg_format.error_msg(f"Could not delete all objects in container '{self.name}'",
                                 self.endpoint)
            return None

        container = self._set_access(delay=delay)

        if not container:
            msg_format.error_msg(f"Failed to set access for container '{self.name}'",
                                 self.endpoint)
            return None

        self._upload_objects(delay=delay)

        msg_format.success_msg(f"Updated container '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(container,
                            self.endpoint,
                            self.debug)

        return container

    def _search(self, delay: float = 0):
        """
        Search for the swift container in OpenStack
        """

        msg_format.general_msg(f"Searching for container '{self.name}'...",
                               self.endpoint)

        result = self.conn.search_containers(name=self.name)
        sleep(delay)

        if result:
            first_container = result[0]
            self.container = first_container

            msg_format.general_msg(f"Found container '{self.name}'",
                                   self.endpoint)
            msg_format.info_msg(first_container,
                                self.endpoint,
                                self.debug)
            return True

        self.container = None
        msg_format.general_msg(f"Didn't find container '{self.name}'",
                               self.endpoint)
        return False

    def _set_access(self,
                    access: str = "public",
                    delay: float = 0) -> object | None:
        """
        Set the swift container access.
        Can be 'public' or 'private'. Default is public.
        """

        msg_format.general_msg(f"Setting container '{self.name}' to {access}...",
                               self.endpoint)

        container = self.conn.set_container_access(name=self.name,
                                              access=access)
        sleep(delay)

        if not container:
            msg_format.error_msg(f"Failed to set {access} for container '{self.name}'",
                                 self.endpoint)
            return None

        msg_format.success_msg(f"Container '{self.name}' is now {access}.",
                               self.endpoint)

        return container

    def _upload_objects(self, delay: float = 0) -> None:
        """
        Upload assets to the swift container
        """

        msg_format.general_msg(f"Uploading objects from '{self.assets_dir}' to container '{self.name}'...",
                               self.endpoint)
        # Collect all the files and folders in the given directory
        files = []
        directories = []
        for (_dir, _ds, _fs) in walk(self.assets_dir):
            if not _ds + _fs:
                directories.append(_dir)
            else:
                files.extend([path.join(_dir, _f) for _f in _fs])

        if directories:
            for directory in directories:
                self.conn.create_directory_marker_object(container=self.name,
                                                    name=directory)
                sleep(delay)

                msg_format.general_msg(f"Created directory marker '{directory}' in '{self.name}'",
                                    self.endpoint)

            msg_format.success_msg(f"Directories created in '{self.name}'",
                                self.endpoint)

        for file in files:
            file = file.replace('\\', '/')
            self.conn.create_object(container=self.name,
                               name=file,
                               filename=file)
            sleep(delay)

            msg_format.general_msg(f"Uploaded object '{file}' to '{self.name}'",
                                   self.endpoint)

        msg_format.success_msg(f"Objects uploaded to '{self.name}'",
                               self.endpoint)

        return None

    def _delete_objects(self,
                        delay: float = 0) -> bool:
        """
        Delete assets from the swift container
        """

        swift_objects = self._list_objects(delay=delay)

        if not swift_objects:
            msg_format.general_msg(f"No objects found in container '{self.name}'",
                                   self.endpoint)
            return True

        msg_format.general_msg(f"Deleting objects from container '{self.name}'...",
                               self.endpoint)

        for swift_object in swift_objects:
            object_name = str(swift_object.name)
            deleted = self.conn.delete_object(self.name,
                                         object_name)
            sleep(delay)

            if deleted:
                msg_format.general_msg(f"Deleted object '{object_name}' from '{self.name}'",
                                       self.endpoint)
            else:
                msg_format.error_msg(f"Failed to delete object '{object_name}' from '{self.name}'",
                                     self.endpoint)
                return False

        msg_format.success_msg(f"Objects deleted from '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(swift_objects,
                            self.endpoint,
                            self.debug)

        return True

    def _list_objects(self,
                      delay: float = 0) -> list | None:
        """
        List the objects in the swift container
        """

        if not self.container:
            msg_format.error_msg(f"Can't list container '{self.name}' because it dosn't exist.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Listing objects in container '{self.name}'...",
                               self.endpoint)

        swift_objects = self.conn.list_objects(self.name)
        sleep(delay)

        if not swift_objects:
            msg_format.general_msg(f"No container objects found in '{self.name}'",
                                   self.endpoint)
        else:
            msg_format.general_msg(f"Objects found in container '{self.name}'",
                                   self.endpoint)
        msg_format.info_msg(swift_objects,
                            self.endpoint,
                            self.debug)

        return swift_objects
