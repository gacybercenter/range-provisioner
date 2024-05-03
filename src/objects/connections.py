"""
Connection Classes
"""
from time import sleep
from typing import Dict, Any, List
import openstack.connection
import guacamole
from objects.parse import expand_instances
from utils import msg_format


class Connection:
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
                 gconn: guacamole.session,
                 name: str,
                 parent_identifier: str = "ROOT",
                 identifier: str | None = None,
                 debug: bool = False):

        self.gconn = gconn
        self.name = name
        self.parent_identifier = parent_identifier
        self.identifier = identifier
        self.debug = debug

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

    def create(self, delay: float = 0):
        """
        Creates a connection
        """
        if self.identifier:
            msg_format.error_msg(
                f"Counld Not Create'{self.name}', {type(self).__name__} Already Exists",
                "Guacamole"
            )
            return None

        if not self.parent_identifier:
            msg_format.error_msg(
                f"Counld Not Create'{self.name}', {type(self).__name__} Parent Not Set",
                "Guacamole"
            )
            return None

        msg_format.general_msg(
            f"Creating {type(self).__name__} '{self.name}' Under '{self.parent_identifier}'",
            "Guacamole"
        )

        response = self._create_connection()

        if isinstance(response, dict):
            self.identifier = response.get('identifier', self.identifier)

        msg_format.info_msg(response,
                            "Guacamole",
                            self.debug)
        sleep(delay)

        return response

    def delete(self, delay: float = 0):
        """
        Deletes a connection
        """
        if not self.identifier:
            msg_format.error_msg(
                f"Counld Not Delete'{self.name}', {type(self).__name__} Does Not Exist",
                "Guacamole"
            )
            return None

        msg_format.general_msg(
            f"Deleting {type(self).__name__} '{self.name}'",
            "Guacamole"
        )

        # Delete the connection
        response = self._delete_connection()

        msg_format.info_msg(response,
                            "Guacamole",
                            self.debug)
        sleep(delay)

        return response

    def update(self, delay: float = 0):
        """
        Updates a connection
        """
        if not self.identifier:
            msg_format.error_msg(
                f"Counld Not Update'{self.name}', {type(self).__name__} Does Not Exist",
                "Guacamole"
            )
            return None

        if not self.parent_identifier:
            msg_format.error_msg(
                f"Counld Not Update'{self.name}', {type(self).__name__} Parent Not Set",
                "Guacamole"
            )
            return None

        msg_format.general_msg(
            f"Updating {type(self).__name__} '{self.name}' Under '{self.parent_identifier}'",
            "Guacamole"
        )

        # Update the connection
        response = self._update_connection()

        if response:
            msg_format.info_msg(response,
                                "Guacamole",
                                self.debug)
        sleep(delay)

        return response

    def _create_connection(self):
        """
        Default implementation for creating a connection
        """
        raise NotImplementedError("Create must be implemented in child class")

    def _delete_connection(self):
        """
        Default implementation for deleting a connection
        """
        raise NotImplementedError("Delete must be implemented in child class")

    def _update_connection(self):
        """
        Default implementation for updating a connection
        """
        raise NotImplementedError("Update must be implemented in child class")

    def detail(self):
        """
        Returns a detailed connection
        """
        raise NotImplementedError("Must be implemented in child class")


class ConnectionGroup(Connection):
    """
    Group of connections

    Args:
        gconn: Connection object
        name: Name of the group
        parent_identifier: Identifier of the parent group
        group_type: Type of the group
        attributes: Attributes of the group
        identifier: Identifier of the group
    """

    def __init__(self,
                 gconn: object,
                 name: str,
                 parent_identifier: str = "ROOT",
                 group_type: str = "ORGANIZATIONAL",
                 attributes: dict | None = None,
                 identifier: str | None = None,
                 debug: bool = False):

        super().__init__(gconn, name, parent_identifier, identifier, debug)

        self.type = group_type
        self.attributes = self._clean_empty_values(attributes)

    def _create_connection(self):
        """
        Default implementation for creating a connection group
        """
        return self.gconn.create_connection_group(self.name,
                                                  self.type,
                                                  self.parent_identifier,
                                                  self.attributes)

    def _delete_connection(self):
        """
        Default implementation for deleting a connection group
        """
        return self.gconn.delete_connection_group(self.identifier)

    def _update_connection(self):
        """
        Default implementation for updating a connection group
        """
        return self.gconn.update_connection_group(self.identifier,
                                                  self.name,
                                                  self.type,
                                                  self.parent_identifier,
                                                  self.attributes)

    def detail(self):
        """
        Gets details of a connection group
        """
        return self.gconn.detail_connection_group_connections(self.identifier)


class ConnectionInstance(Connection):
    """
    Connections

    Args:
        gconn: Connection object
        name: Name of the group
        parent_identifier: Identifier of the parent group
        group_type: Type of the group
        attributes: Attributes of the group
        identifier: Identifier of the group
    """

    def __init__(self,
                 gconn: object,
                 protocol: str,
                 name: str,
                 parent_identifier: str,
                 parameters: dict | None = None,
                 attributes: dict | None = None,
                 identifier: str | None = None,
                 debug: bool = False):

        super().__init__(gconn, name, parent_identifier, identifier, debug)

        self.protocol = protocol
        self.attributes = self._clean_empty_values(attributes)
        self.parameters = self._clean_empty_values(parameters)

    def _create_connection(self):
        """
        Default implementation for creating a connection
        """
        return self.gconn.manage_connection(self.protocol,
                                            self.name,
                                            self.parent_identifier,
                                            None,
                                            self.parameters,
                                            self.attributes)

    def _delete_connection(self):
        """
        Default implementation for deleting a connection
        """
        return self.gconn.delete_connection(self.identifier)

    def _update_connection(self):
        """
        Default implementation for updating a connection
        """
        return self.gconn.manage_connection(self.protocol,
                                            self.name,
                                            self.parent_identifier,
                                            self.identifier,
                                            self.parameters,
                                            self.attributes)

    def detail(self):
        """
        Gets details of a connection
        """
        self.parameters = self.gconn.detail_connection(
            self.identifier, 'parameters'
        )
        return self.parameters


class SharingProfile(Connection):
    """
    Sharing connections

    Args:
        gconn: Connection object
        name: Name of the group
        parent_identifier: Identifier of the parent group
        group_type: Type of the group
        attributes: Attributes of the group
        identifier: Identifier of the group
    """

    def __init__(self,
                 gconn: object,
                 name: str,
                 parent_identifier: str,
                 parameters: dict | None = None,
                 identifier: str | None = None,
                 debug: bool = False):

        super().__init__(gconn, name, parent_identifier, identifier, debug)

        self.parameters = self.parameters = self._clean_empty_values(
            parameters)

    def _create_connection(self):
        """
        Default implementation for creating a connection
        """
        return self.gconn.create_sharing_profile(self.parent_identifier,
                                                 self.name,
                                                 self.parameters,)

    def _delete_connection(self):
        """
        Default implementation for deleting a connection
        """
        return self.gconn.delete_sharing_profile(self.identifier)

    def _update_connection(self):
        """
        Default implementation for updating a connection
        """
        return self.gconn.update_sharing_profile(self.parent_identifier,
                                                 self.name,
                                                 self.identifier,
                                                 self.parameters,)

    def detail(self):
        """
        Gets details of a sharing profile
        """
        self.parameters = self.gconn.detail_sharing_profile(
            self.identifier, 'parameters'
        )
        return self.parameters


class HeatInstances:
    """
    Provides a list of instances for a given stack
    """

    def __init__(self,
                 oconn: openstack.connection.Connection,
                 stack_names: list,
                 debug: bool = False):

        self.oconn = oconn
        self.stack_names = set(stack_names)
        self.servers = []
        self.addresses = {}
        self.debug = debug

        msg_format.general_msg(f"Finding Servers in {stack_names}", "Heat")
        for stack_name in stack_names:
            stack = self.find_stack_by_name(stack_name)
            servers = self.get_servers_in_stack(stack)
            self.servers.extend(servers)

        self.addresses = self.get_addresses(self.servers)

    def find_stack_by_name(self,
                           stack_name):
        """
        Find the stack by name
        """
        stack = self.oconn.orchestration.find_stack(stack_name)
        if not stack:
            # msg_format.error_msg(f"Could Not Find Stack '{stack_name}'",
            #                      "Heat")
            raise Exception(f"Could Not Find Stack '{stack_name}'")

        msg_format.info_msg(stack,
                            "Heat",
                            self.debug)
        return stack

    def get_servers_in_stack(self, stack=None):
        """
        Get all servers in the stack
        """
        if not stack:
            return []

        # Method to recursively get server resources
        def get_server_resources(resources):
            server_resources = []
            for res in resources:
                # Check if resource is a server
                if res.resource_type == 'OS::Nova::Server':
                    server_resources.append(res)
                # Check if resource is a Resource Group and recurse
                elif res.resource_type == 'OS::Heat::ResourceGroup':
                    nested_resources = self.oconn.orchestration.resources(
                        res.physical_resource_id)
                    server_resources.extend(
                        get_server_resources(nested_resources))
            return server_resources

        # List all top-level resources in the stack
        top_level_resources = self.oconn.orchestration.resources(stack.id)
        all_server_resources = get_server_resources(top_level_resources)

        # Get server objects using the physical_resource_id (which is the server id)
        servers = [
            self.oconn.compute.get_server(res.physical_resource_id)
            for res in all_server_resources
        ]

        return servers

    def get_addresses(self, servers):
        """
        Get all addresses for all servers in the stack
        """
        addresses = {
            server.name: list(server.addresses.values())[0][0]['addr']
            for server in servers
        }
        msg_format.info_msg(addresses,
                            "Heat",
                            self.debug)
        return addresses


class CurrentConnections():
    """
    An object that holds connection groups, instances and sharing profiles
    """

    def __init__(self,
                 gconn: guacamole.session,
                 parent_identifier: str = 'ROOT',
                 debug: bool = False):

        self.gconn = gconn
        self.parent_identifier = parent_identifier or 'ROOT'
        self.debug = debug
        if self.parent_identifier == 'ROOT':
            msg_format.general_msg("Getting All Current Connections, Parent DNE",
                                   "Guacamole")
        else:
            msg_format.general_msg(f"Getting Current Connections Under ID '{parent_identifier}'",
                                   "Guacamole")
        self.tree = gconn.detail_connection_group_connections(
            parent_identifier
        )
        self.connections = self.extract_connections(self.tree)

    def extract_connections(self,
                            obj: dict,
                            parent='ROOT') -> list[Connection]:
        """
        Recursively walks through an object and extracts connection groups,
        connections, and sharing groups.

        Parameters:
        obj (dict): The object to extract groups and connections from.

        Returns:
        object: The extracted connection groups, connections, and sharing groups.
        """

        conns = []

        if isinstance(obj, dict):
            if obj.get('name'):
                conn = obj.copy()
                conn['parent'] = parent
                if conn.get('childConnectionGroups'):
                    del conn['childConnectionGroups']
                if conn.get('childConnections'):
                    del conn['childConnections']
                if conn.get('sharingProfiles'):
                    del conn['sharingProfiles']

                conn_object = self.conn_object(conn)
                if conn_object:
                    conns.append(conn_object)

            for value in obj.values():
                if isinstance(value, (dict, list)):
                    child_conns = self.extract_connections(value,
                                                           parent)
                    conns.extend(child_conns)

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    child_conns = self.extract_connections(item,
                                                           parent)
                    conns.extend(child_conns)
        return conns

    def conn_object(self,
                    dictionary: dict) -> Connection | None:
        """
        Returns a connection object from a dictionary
        """
        if dictionary.get('identifier') == 'ROOT':
            return None

        conn = None
        if dictionary.get('type'):
            conn = ConnectionGroup(self.gconn,
                                   dictionary['name'],
                                   dictionary['parentIdentifier'],
                                   dictionary['type'],
                                   dictionary.get('attributes'),
                                   dictionary['identifier'],
                                   debug=self.debug)
        if dictionary.get('protocol'):
            conn = ConnectionInstance(self.gconn,
                                      dictionary['protocol'],
                                      dictionary['name'],
                                      dictionary['parentIdentifier'],
                                      dictionary.get('parameters'),
                                      dictionary.get('attributes'),
                                      dictionary['identifier'],
                                      debug=self.debug)
            conn.detail()
        if dictionary.get('primaryConnectionIdentifier'):
            conn = SharingProfile(self.gconn,
                                  dictionary['name'],
                                  dictionary['primaryConnectionIdentifier'],
                                  dictionary.get('parameters'),
                                  dictionary['identifier'],
                                  debug=self.debug)
            conn.detail()

        msg_format.info_msg(f"Found {type(conn).__name__} '{conn.name}'",
                            "Guacamole",
                            self.debug)
        return conn


class NewConnections():
    """
    An object that holds connection groups, instances and sharing profiles
    """

    def __init__(self,
                 gconn: guacamole.session,
                 oconn: openstack.connect,
                 conn_data: dict,
                 debug: bool = False):

        self.gconn = gconn
        self.oconn = oconn
        self.conn_data = conn_data
        self.debug = debug

        self.stacks = conn_data.get('stacks') or list(
            conn_data['groups'].keys())
        self.addresses = HeatInstances(oconn, self.stacks, debug).addresses
        self.parent_identifiers: List[str] = []
        self.connections: List[Connection] = []
        self.current_connections: List[Connection] = []
        parent_ids = self._find_root_ids()
        parent_id_map = {
            parent: parent_ids.get(parent)
            for parent, data in conn_data['groups'].items()
            if data.get('parent') == 'ROOT'
        }

        self.defaults = conn_data['defaults']

        self._create_connection_groups(conn_data, parent_id_map)
        self._create_connections(conn_data)

    def create(self, delay: float = 0):
        """
        Creates the Guacamole connections
        """
        msg_format.general_msg("Creating Connections",
                               "Guacamole")
        identifier_map = {}
        for conn in self.connections:
            if not conn.parent_identifier.isnumeric():
                conn.parent_identifier = identifier_map.get(
                    conn.parent_identifier, 'ROOT'
                )
            conn.create(delay)
            identifier_map[conn.name] = conn.identifier

    def delete(self, delay: float = 0):
        """
        Deletes the Guacamole connections
        """
        msg_format.general_msg("Deleting Connections",
                               "Guacamole")
        for conn in self.connections:
            if conn.identifier in self.parent_identifiers:
                conn.delete(delay)

    def update(self, delay: float = 0):
        """
        Updates the Guacamole connections
        """
        msg_format.general_msg("Updating Connections",
                               "Guacamole")
        conns_by_ids = {}
        conn_map = {'ROOT': 'ROOT'}
        for conn in self.current_connections:
            conns_by_ids[conn.identifier] = conn
            conn_map.setdefault(conn.name, conn.identifier)

        for conn in self.connections:
            if conn.parent_identifier and not conn.parent_identifier.isnumeric():
                conn.parent_identifier = conn_map.get(conn.parent_identifier)
            if not conn.identifier:
                conn.identifier = conn_map.get(conn.name)

            old_identifier = conn_map.get(conn.name)
            if old_identifier:
                old_conn = conns_by_ids.get(old_identifier)
                self.current_connections.remove(old_conn)
                if old_conn == conn:
                    msg_format.info_msg(f"No Changes For {type(conn).__name__} '{conn.name}'",
                                        "Guacamole",
                                        self.debug)
                    continue
                conn.update(delay)
            else:
                conn.create(delay)
                conn_map[conn.name] = conn.identifier

        for conn in self.current_connections:
            if conn not in self.connections:
                conn.delete(delay)

    def _find_root_ids(self) -> dict:
        conn_groups = self.gconn.list_connection_groups()
        root_ids = {}
        for identifier, group in conn_groups.items():
            if group.get('parentIdentifier') == 'ROOT':
                root_ids[group['name']] = identifier
        return root_ids

    def _create_connection_groups(self,
                                  conn_data: dict,
                                  parent_id_map: dict) -> None:
        msg_format.general_msg("Generating New Connection Groups",
                               "Guacamole")
        for name, data in conn_data['groups'].items():
            # Add current connections under parent
            if data.get('parent') == 'ROOT':
                identifier = parent_id_map.get(name)
                if identifier:
                    self.current_connections.extend(
                        CurrentConnections(self.gconn,
                                           identifier,
                                           debug=self.debug).connections
                    )
                    self.parent_identifiers.append(identifier)
            data = expand_instances(
                self.defaults.get('groups', {}), data
            )
            for d in data:
                self.connections.append(
                    self._create_connection_group(d, name)
                )

    def _create_connections(self,
                            conn_data: dict) -> None:
        msg_format.general_msg("Generating New Connections and Sharing Profiles",
                               "Guacamole")
        for template, data in conn_data['connectionTemplates'].items():
            data = expand_instances(
                self.defaults.get('connectionTemplates', {}), data
            )
            for d in data:
                pattern = d.get("pattern", template)
                found = False
                for name, address in self.addresses.items():
                    if pattern in name:
                        self.connections.extend(
                            self._create_connection_instances(d, name, address)
                        )
                        found = True
                if not found:
                    msg_format.error_msg(
                        f"Pattern '{pattern}' was not found in Heat instances",
                        "Guacamole"
                    )

    def _create_connection_group(self,
                                 data: dict,
                                 name: str) -> ConnectionGroup:
        group = ConnectionGroup(self.gconn,
                                data.get('name', name),
                                data.get('parent'),
                                data.get('type', 'ORGANIZATIONAL'),
                                data.get('attributes'),
                                None,
                                debug=self.debug)
        msg_format.info_msg(group,
                            "Guacamole",
                            self.debug)
        return group

    def _create_connection_instances(self,
                                     data: dict,
                                     name: str,
                                     address: str) -> List[ConnectionInstance]:
        attributes = data.get('attributes') or {}
        parameters = data.get('parameters') or {}
        sharings = data.get('sharingProfiles') or {}
        param_copy = {
            **parameters,
            'hostname': address
        }
        attr_copy = {
            **attributes,
            'guacd-hostname': self._get_guacd_hostname(attributes)
        }
        instance = ConnectionInstance(self.gconn,
                                      data.get('protocol', 'ssh'),
                                      data.get('name', name),
                                      data.get('parent', 'ROOT'),
                                      param_copy,
                                      attr_copy,
                                      debug=self.debug)
        msg_format.info_msg(instance,
                            "Guacamole",
                            self.debug)
        instances = [instance]
        if sharings:
            if isinstance(sharings, dict):
                sharings = [sharings]
            instances.extend(
                self._create_sharing_profiles(sharings, name)
            )
        return instances

    def _get_guacd_hostname(self,
                            attributes: dict) -> str:
        guacd_host = attributes.get('guacd-hostname')
        if guacd_host:
            return next(
                (
                    addr
                    for name, addr in self.addresses.items()
                    if guacd_host in name
                ), guacd_host
            )
        return ''

    def _create_sharing_profiles(self,
                                 sharings: List[dict],
                                 name: str) -> List[SharingProfile]:
        sharing_profiles = []
        for sharing in sharings:
            profile = SharingProfile(self.gconn,
                                     sharing.get('name', f"{name}.share"),
                                     name,
                                     sharing.get('parameters'),
                                     debug=self.debug)
            msg_format.info_msg(profile,
                                "Guacamole",
                                self.debug)
            sharing_profiles.append(profile)

        return sharing_profiles
