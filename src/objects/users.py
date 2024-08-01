"""
User Classes
"""

import re
from time import sleep
from secrets import choice
from string import ascii_letters, digits
from typing import List, Dict, Set, Tuple, Any
import guacamole
from objects.connections import ConnectionGroup, ConnectionInstance, SharingProfile, Connection
from objects.parse import clean_dict, recursive_update
from utils import msg_format


class User:
    """
    User

    Args:
        gconn: Connection object
        username: Name of the user
        password: Password of the user
        attributes: Attributes of the user
        permissions: Permissions of the user
    """

    def __init__(self,
                 gconn: guacamole.session,
                 username: str,
                 password: str | None = None,
                 attributes: dict | None = None,
                 permissions: dict | None = None,
                 debug: bool = False):

        self.gconn = gconn
        self.username = username
        self.password = password if password else self._generate_password(16)
        self.attributes = self._clean_empty_values(attributes)
        self.permissions = self._flatten_permissions(
            self._clean_empty_values(permissions)
        )
        self.permissions['userPermissions'] = [username]
        self.debug = debug

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

    @staticmethod
    def _generate_password(length: int = 16) -> str:
        """
        Generate a random password consisting of 16 characters.

        Returns:
            str: The generated password.
        """
        alphabet = ascii_letters + digits
        return ''.join(
            choice(alphabet) for _ in range(length)
        )

    @staticmethod
    def _clean_empty_values(d: Dict[str, Any] | List[str]) -> Dict[str, Any]:
        """
        Removes None and empty values from a dictionary or a list,
        and returns a sorted object.
        """
        if not isinstance(d, (dict, list)):
            return {}

        if isinstance(d, list):
            return sorted([
                str(item)
                for item in d
                if item
            ])

        return_dict = {}
        for key, value in sorted(d.items()):
            if value:
                value = str(value) if isinstance(value, int) else value
                return_dict[str(key)] = value

        return return_dict

    @staticmethod
    def _flatten_permissions(permissions: dict) -> dict:
        """
        Flattens permissions to a single level.
        """
        if not isinstance(permissions, dict):
            return {}

        flattened_permissions = {}

        for category, permission in permissions.items():
            flattened_permissions[category] = sorted([
                perm
                for perm in permission
                if perm
            ])

        return flattened_permissions

    def create(self, delay: float = 0):
        """
        Creates a connection group
        """
        result = self.gconn.create_user(self.username,
                                        self.password,
                                        self.attributes)
        msg_format.info_msg(result,
                            "Guacamole",
                            self.debug)
        sleep(delay)
        self.manage_permissions()
        msg_format.general_msg(f"Created {self.username}",
                               "Guacamole")
        sleep(delay)

        return result

    def delete(self, delay: float = 0):
        """
        Deletes a user
        """
        result = self.gconn.delete_user(self.username)
        msg_format.info_msg(result,
                            "Guacamole",
                            self.debug)
        msg_format.general_msg(f"Deleted {self.username}",
                               "Guacamole")
        sleep(delay)

        return result

    def update(self,
               old_perms: dict | None = None,
               delay: float = 0):
        """
        Updates a user
        """
        old_perms = old_perms if old_perms else {}
        result = self.gconn.update_user(self.username,
                                        self.attributes)
        msg_format.info_msg(result,
                            "Guacamole",
                            self.debug)
        sleep(delay)
        self.manage_permissions(old_perms)
        msg_format.general_msg(f"Updated {self.username}",
                               "Guacamole")
        sleep(delay)

        return result

    def detail(self):
        """
        Returns user details
        """
        return self.gconn.detail_user_permissions(self.username)

    def manage_permissions(self,
                           old_perms: dict | None = None):
        """
        Sets permissions
        """
        if old_perms:
            perms_to_add, perms_to_remove = self._resolve_permissions(
                old_perms,
                self.permissions
            )
        else:
            perms_to_add = self.permissions
            perms_to_remove = {}

        self._update_category_permissions(perms_to_add,
                                          perms_to_remove)

    def _resolve_permissions(self, old_perms: dict, new_perms: dict) -> dict:
        """
        Find the difference between two sets of permissions.

        Args:
            old_perms (dict): The old set of permissions.
            new_perms (dict): The new set of permissions.

        Returns:
            dict: Permissions that need to be removed and added.
        """
        perms_changes = {'add': {}, 'remove': {}}
        categories = set(old_perms) | set(new_perms)
        for category in categories:
            if category == 'userPermissions':
                continue
            new_perm_set = set(new_perms.get(category, []))
            old_perm_set = set(old_perms.get(category, []))
            perms_changes['add'][category] = list(new_perm_set - old_perm_set)
            perms_changes['remove'][category] = list(old_perm_set - new_perm_set)

        return perms_changes['add'], perms_changes['remove']
    
    def _update_category_permissions(self,
                                     perms_to_add: dict,
                                     perms_to_remove: dict):
        connection_types = {
            'connectionGroupPermissions': 'group',
            'connectionPermissions': 'connection',
            'sharingProfilePermissions': 'sharing profile',
            'userGroupPermissions': 'user group',
            'systemPermissions': 'system',
        }
        for category, connection_type in connection_types.items():
            operations = {
                'add': perms_to_add.get(category, []),
                'remove': perms_to_remove.get(category, [])
            }
            for operation, permission in operations.items():
                if not permission:
                    continue

                if connection_type in ['group', 'connection', 'sharing profile']:
                    result = self.gconn.update_connection_permissions(self.username,
                                                                    permission,
                                                                    operation,
                                                                    connection_type)
                elif connection_type == 'user group':
                    result = self.gconn.update_user_group(self.username,
                                                        permission,
                                                        operation)
                elif connection_type == 'system':
                    result = self.gconn.update_user_permissions(self.username,
                                                                permission,
                                                                operation)
                if result:
                    msg_format.info_msg(result,
                                        "Guacamole",
                                        self.debug)


class CurrentUsers():
    """
    Current user object
    """

    def __init__(self,
                 gconn: guacamole.session,
                 organization: str = '',
                 debug: bool = False) -> None:

        self.gconn = gconn
        self.organization = organization
        self.debug = debug

        msg_format.general_msg("Getting Current Users",
                               "Guacamole")
        self.users = [
            self._create_user(user_data)
            for user_data in self._get_user_data()
        ]
        msg_format.info_msg(self.users,
                            "Guacamole",
                            self.debug)

    def _get_user_data(self) -> List[dict]:
        users_data = self.gconn.list_users()
        if self.organization:
            return [
                user
                for user in users_data.values()
                if user['attributes']['guac-organization'] == self.organization
            ]
        return list(users_data.values())

    def _create_user(self, user_data: dict) -> User:
        user_data['permissions'] = self.gconn.detail_user_permissions(
            user_data['username']
        )
        user_data = clean_dict(user_data)
        user = User(self.gconn,
                    user_data['username'],
                    '*',
                    user_data.get('attributes'),
                    user_data.get('permissions'),
                    debug=self.debug)

        return user

    def delete(self, delay: float = 0) -> None:
        """
        Deletes the Guacamole users
        """
        msg_format.general_msg("Deleting Users",
                               "Guacamole")
        for user in self.users:
            user.delete(delay)

class NewUsers():
    """
    An object that holds connection groups, instances and sharing profiles
    """

    def __init__(self,
                 gconn: guacamole.session,
                 guac_data: dict,
                 organization: str = '',
                 connections: List[Connection] | None = None,
                 debug: bool = False) -> None:

        self.gconn = gconn
        self.guac_data = guac_data
        self.organization = organization
        self.users: List[User] = []
        self.defaults = guac_data.get('defaults', {})
        self.debug = debug
        self.current_users = CurrentUsers(
            gconn, organization, debug=debug
        ).users

        self.connection_groups: List[ConnectionGroup] = []
        self.connection_instances: List[ConnectionInstance] = []
        self.sharing_profiles: List[SharingProfile] = []
        for connection in connections:
            if isinstance(connection, ConnectionGroup):
                self.connection_groups.append(connection)
            elif isinstance(connection, ConnectionInstance):
                self.connection_instances.append(connection)
            elif isinstance(connection, SharingProfile):
                self.sharing_profiles.append(connection)

        self._create_users()
        self._update_passwords()

    def create(self, delay: float = 0) -> None:
        """
        Creates the Guacamole users
        """
        msg_format.general_msg("Creating Users",
                               "Guacamole")
        for user in self.users:
            if user.password != '*':
                user.create(delay)

    def delete(self, delay: float = 0) -> None:
        """
        Deletes the Guacamole users
        """
        msg_format.general_msg("Deleting Users",
                               "Guacamole")
        for user in self.current_users:
            if user.password == '*':
                user.delete(delay)

    def update(self, delay: float = 0) -> None:
        """
        Updates the Guacamole users
        """
        msg_format.general_msg("Updating Users",
                               "Guacamole")
        current_users_by_username = {
            user.username: user for user in self.current_users}
        for user in self.users:
            old_user = current_users_by_username.get(user.username)
            if old_user and old_user in self.current_users:
                self.current_users.remove(old_user)
                if old_user == user:
                    msg_format.info_msg(f"No Changes For {type(self).__name__} '{user.username}'",
                                           "Guacamole",
                                           self.debug)
                    continue
                user.update(old_user.permissions, delay)
            else:
                user.create(delay)
        for user in self.current_users:
            if user not in self.users:
                user.delete(delay)

    def _create_users(self) -> None:
        if not self.guac_data.get('users'):
            msg_format.general_msg("No Users Specified",
                                    "Guacamole")
            return

        msg_format.general_msg("Generating New Users",
                               "Guacamole")
        defaults = self.defaults.get('users') or {}
        for name, data in self.guac_data['users'].items():
            new_data = recursive_update(defaults, data)

            permissions = new_data.get('permissions') or {}
            attributes = new_data.get('attributes') or {}
            attributes['guac-organization'] = self.organization

            conn_perms = permissions.get('connectionPermissions') or []
            groups, conns, sharings = self._resolve_connections(conn_perms)
            permissions['connectionGroupPermissions'] = groups
            permissions['connectionPermissions'] = conns
            permissions['sharingProfilePermissions'] = sharings
            self.users.append(
                User(self.gconn,
                        new_data.get('username', name),
                        new_data.get('password'),
                        attributes,
                        permissions,
                        debug=self.debug)
            )

        msg_format.info_msg(self.users,
                            "Guacamole",
                            self.debug)

    def _resolve_connections(self, names: List[str]) -> Tuple[List['ConnectionInstance'], List['ConnectionInstance'], List['SharingProfile']]:
        """
        Recursively search for connections based on a list of names
        and return all parent groups in the hierarchy.

        Parameters:
        - names (list): The names of the connections to resolve.
        
        Returns:
        - list: A list of all parent group ids in the hierarchy.
        - list: A list of all connection ids in the hierarchy.
        - list: A list of all sharing profile ids in the hierarchy.
        """

        groups: Set[ConnectionGroup] = set()
        connections: Set[ConnectionInstance] = set()
        sharing_profiles: Set[SharingProfile] = set()
        patterns = [re.compile(pattern_str) for pattern_str in names]

        for connection in self.connection_instances:
            if any(pattern.search(connection.name) for pattern in patterns):
                connections.add(connection)

        for connection in connections:
            parent = connection.parent_identifier
            identifier = connection.identifier
            groups.update(self._resolve_groups(parent))
            sharing_profiles.update(self._resolve_sharing_profiles(identifier))

        group_ids = [group.identifier for group in groups]
        connection_ids = [connection.identifier for connection in connections]
        sharing_profile_ids = [sharing_profile.identifier for sharing_profile in sharing_profiles]

        return group_ids, connection_ids, sharing_profile_ids

    def _resolve_groups(self, parent_identifier: 'str') -> Set['ConnectionGroup']:
        """
        Recursively search for connection groups based on a parent identifier
        and return all parent groups in the hierarchy.

        Parameters:
        - parent_identifier (str): The the parent group to resolve.

        Returns:
        - set: A set of all parent groups in the hierarchy.
        """

        if parent_identifier == 'ROOT':
            return set()

        groups = set()
        for connection in self.connection_groups:
            if connection.identifier == parent_identifier:
                groups.add(connection)
                groups.update(self._resolve_groups(connection))

        return groups

    def _resolve_sharing_profiles(self, identifier: 'str') -> Set['SharingProfile']:
        """
        Recursively search for sharing profiles based on a parent
        and return all sharing profiles in the hierarchy.

        Parameters:
        - identifier (str): The the connection to resolve.

        Returns:
        - set: A set of all sharing profiles in the hierarchy.
        """

        sharing_profiles = set()
        for sharing_profile in self.sharing_profiles:
            if sharing_profile.parent_identifier == identifier:
                sharing_profiles.add(sharing_profile)

        return sharing_profiles


    def _update_passwords(self) -> None:
        for new_user in self.users:
            for old_user in self.current_users:
                if new_user.username == old_user.username:
                    new_user.password = old_user.password
                    break
