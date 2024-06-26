"""
Connection Classes
"""
from time import sleep
from typing import Dict, Any, List
import re
import openstack.connection
import guacamole
from objects.parse import recursive_update
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
                 stack_name: str,
                 debug: bool = False):

        self.oconn = oconn
        self.stack_name = stack_name
        self.debug = debug

        msg_format.general_msg(f"Finding Servers in {stack_name}", "Heat")
        stack = self.find_stack_by_name(stack_name)
        self.servers = self.get_servers_in_stack(stack)
        self.addresses = self.get_addresses(self.servers)

    def find_stack_by_name(self,
                           stack_name):
        """
        Find the stack by name
        """
        stack = self.oconn.orchestration.find_stack(stack_name)
        if not stack:
            msg_format.error_msg(f"Could Not Find Stack '{stack_name}'",
                                 "Heat")
            # raise Exception(f"Could Not Find Stack '{stack_name}'")

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
        addresses = {}
        for server in servers:
            ip_addr = server.addresses.get('public')[0]['addr']
            if not ip_addr:
                ip_addr = list(server.addresses.values())[0][0]['addr']
            addresses[server.name] = ip_addr
            
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
                 names: list | str | None = None,
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

        connections = self.extract_connections(self.tree)
        if isinstance(names, str):
            self.connections = [
                conn
                for conn in connections
                if names == conn.name
            ]
        elif isinstance(names, list):
            self.connections = [
                conn
                for conn in connections
                if any(name == conn.name for name in names)
            ]
        else:
            self.connections = connections

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

    def delete(self, delay: float = 0):
        """
        Deletes the Guacamole connections
        """
        msg_format.general_msg("Deleting Connections",
                               "Guacamole")
        for conn in self.connections:
            conn.delete(delay)


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

        self.parent_groups: set[ConnectionGroup] = set()
        self.connections: List[Connection] = []
        self.current_connections: set[Connection] = set()
        self.defaults = conn_data.get('defaults') or {}
        self._find_current_conns()
        self._create_connection_groups()

        stacks = conn_data.get('stacks')
        if not stacks:
            stacks = conn_data['groups'].keys()

        for stack in stacks:
            addresses = HeatInstances(oconn, stack, debug).addresses
            self._create_connections(addresses, stack)

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
        for groups in self.parent_groups:
            groups.delete(delay)

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
                if old_conn and old_conn in self.current_connections:
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

    def _find_current_conns(self) -> dict:
        new_groups = self.conn_data.get('groups', self.conn_data['stacks'])
        if not new_groups:
            return

        conn_groups = self.gconn.list_connection_groups()
        for identifier, group in conn_groups.items():
            if group['name'] in new_groups and group['parentIdentifier'] == 'ROOT':
                parent_group = ConnectionGroup(self.gconn,
                                               group['name'],
                                               'ROOT',
                                               group['type'],
                                               group.get('attributes'),
                                               identifier,
                                               debug=self.debug)
                current_conns = CurrentConnections(self.gconn,
                                                    identifier,
                                                    None,
                                                    debug=self.debug).connections
                self.current_connections.update(current_conns)
                self.parent_groups.add(parent_group)

    def _create_connection_groups(self) -> None:
        if not self.conn_data.get('groups'):
            msg_format.general_msg("No Connection Groups Specified",
                                    "Guacamole")
            return

        msg_format.general_msg("Generating New Connection Groups",
                               "Guacamole")
        defaults = self.defaults.get('groups') or {}
        for name, data in self.conn_data['groups'].items():
            new_data = recursive_update(defaults, data)
            conn_group = self._create_connection_group(new_data, name)
            self.connections.append(conn_group)

    def _create_connections(self,
                            addresses: dict,
                            stack: str | None = None) -> None:
        if not self.conn_data.get('connectionTemplates'):
            msg_format.general_msg("No Connection Instances Specified",
                                    "Guacamole")
            return

        msg_format.general_msg("Generating New Connections and Sharing Profiles",
                               "Guacamole")
        defaults = self.defaults.get('connectionTemplates') or {}
        for template, data in self.conn_data['connectionTemplates'].items():
            new_data = recursive_update(defaults, data)
            found = False
            pattern = re.compile(new_data.get("pattern", template))
            for name, address in addresses.items():
                if pattern.search(name):
                    attibutes = new_data.get('attributes') or {}
                    guacd_name = attibutes.get('guacd-hostname')
                    guacd_ip = self._get_guacd_ip(guacd_name,
                                                    addresses)
                    conn_instances = self._create_connection_instances(new_data,
                                                                        name,
                                                                        address,
                                                                        guacd_ip)
                    self.connections.extend(conn_instances)
                    found = True
            if not found and stack:
                msg_format.info_msg(f"Pattern '{pattern}' was not found in stack '{stack}'",
                                        "Guacamole",
                                        self.debug)


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
                                     address: str,
                                     guacd_host: str) -> List[ConnectionInstance]:
        attributes = data.get('attributes') or {}
        parameters = data.get('parameters') or {}
        sharings = data.get('sharingProfiles') or {}
        param_copy = {
            **parameters,
            'hostname': address
        }
        attr_copy = {
            **attributes,
            'guacd-hostname': guacd_host
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

    def _get_guacd_ip(self,
                            guacd_host: str,
                            addresses: dict) -> str:

        if guacd_host:
            return next(
                (
                    addr
                    for name, addr in addresses.items()
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





# class NewConnections():
#     """
#     An object that holds connection groups, instances and sharing profiles
#     """

#     def __init__(self,
#                  gconn: guacamole.session,
#                  oconn: openstack.connect,
#                  conn_data: dict,
#                  debug: bool = False):

#         self.gconn = gconn
#         self.oconn = oconn
#         self.conn_data = conn_data
#         self.debug = debug

#     def create(self, delay: float = 0):
#         self._create_or_update_connections(delay, "create")

#     def update(self, delay: float = 0):
#         self._create_or_update_connections(delay, "update")

#     def delete(self, delay: float = 0):
#         self._delete_connections(delay)

#     def _create_or_update_connections(self, delay: float, action: str):
#         msg_format.general_msg(f"{action.title()} Connections",
#                                 "Guacamole")
#         action_fn = self._create_connection if action == "create" else self._update_connection
#         for conn in self._generate_connections():
#             action_fn(conn, delay)

#     def _delete_connections(self, delay: float):
#         msg_format.general_msg("Deleting Connections",
#                                "Guacamole")
#         for groups in self._get_parent_groups():
#             groups.delete(delay)

#     def _generate_connections(self):
#         conn_data = self.conn_data
#         stacks = conn_data.get('stacks')
#         if not stacks:
#             stacks = list(conn_data['groups'].keys())

#         addresses = self._get_addresses(stacks)
#         yield from self._create_connections(addresses)

#     def _get_parent_groups(self):
#         conn_data = self.conn_data
#         self._find_current_conns(conn_data)
#         yield from self._create_connection_groups(conn_data)

#     def _get_addresses(self, stacks):
#         oconn = self.oconn
#         return {name: HeatInstances(oconn, stack, self.debug).addresses
#                 for stack in stacks
#                 for name in HeatInstances(oconn, stack, self.debug).names}

#     def _create_connection(self, conn, delay):
#         conn.create(delay)

#     def _update_connection(self, conn, delay):
#         old_conn = self._get_old_connection(conn)
#         if old_conn:
#             self._delete_connection(old_conn, delay)
#         conn.create(delay)

#     def _delete_connection(self, conn, delay):
#         conn.delete(delay)

#     def _get_old_connection(self, conn):
#         return next((c for c in self.current_connections
#                      if c.name == conn.name), None)

