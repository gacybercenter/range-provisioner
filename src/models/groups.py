
"""
Class for connection groups
"""
import yaml
import guacamole
import openstack


class Connection:
    """
    Connection
    
    Args:
        gconn: Connection object
        name: Name of the connection
        protocol: Protocol of the connection
        identifier: Identifier of the connection
    """
    def __init__(self,
                 gconn: object,
                 name: str,
                 parent_identifier: str = "ROOT",
                 identifier: str | None = None):

        self.gconn = gconn
        self.name = name
        self.parent_identifier = parent_identifier
        self.identifier = identifier
        self.active_connections = '0'

    def __hash__(self):
        return hash(self.identifier + self.name + self.parent_identifier)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        string = 'Connection('
        for key, value in self.__dict__.items():
            string += f'{key}: {value}\n'
        string += ')'
        return string

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        """
        Returns a dictionary representation of the connection group
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if value
        }


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
                 identifier: str | None = None):

        super().__init__(gconn, name, parent_identifier, identifier)

        if attributes is None:
            attributes = {}
        self.attributes = {
            'enable-session-affinity': attributes.get('enable-session-affinity', ''),
            'max-connections': attributes.get('max-connections', '50'),
            'max-connections-per-user': attributes.get('max-connections-per-user', '10')
        }
        self.type = group_type

    def create(self):
        """
        Creates a connection group
        """
        gconn = self.gconn
        if self.identifier:
            return gconn.update_connection_group(self.identifier,
                                                     self.name,
                                                     self.type,
                                                     self.parent_identifier,
                                                     self.attributes)

        response = gconn.create_connection_group(self.name,
                                                    self.type,
                                                    self.parent_identifier,
                                                    self.attributes)
        if isinstance(response, dict):
            self.identifier = response.get('identifier')

        # if not self.identifier:
        #     groups = gconn.list_connection_groups()
        #     for group in groups.values():
        #         if group.get('name') == self.name and group.get('parentIdentifier') == self.parent_identifier:
        #             self.identifier = group.get('identifier')
        #             return group

        return response


    def delete(self):
        """
        Deletes a connection group
        """
        if not self.identifier:
            return None

        gconn = self.gconn
        return gconn.delete_connection_group(self.identifier)


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
                 identifier: str | None = None):

        super().__init__(gconn, name, parent_identifier, identifier)

        if parameters is None:
            self.parameters = {}
        if attributes is None:
            self.attributes = {}
        self.protocol = protocol

    def create(self):
        """
        Creates a connection group
        """
        gconn = self.gconn
        response = gconn.manage_connection(self.protocol,
                                        self.name,
                                        self.parent_identifier,
                                        self.identifier,
                                        self.parameters,
                                        self.attributes)

        if isinstance(response, dict) and not self.identifier:
            self.identifier = response.get('identifier')

        return response


    def delete(self):
        """
        Deletes a connection group
        """
        if not self.identifier:
            return None

        gconn = self.gconn
        return gconn.delete_connection(self.identifier)


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
                 attributes: dict | None = None,
                 identifier: str | None = None):

        super().__init__(gconn, name, parent_identifier, identifier)

        if not attributes:
            attributes = {}
        self.attributes = {
            'read-only': attributes.get('read-only', 'false'),
        }

    def create(self):
        """
        Creates a connection group
        """
        gconn = self.gconn
        if self.identifier:
            return gconn.update_connection_group(self.parent_identifier,
                                                     self.name,
                                                     self.identifier,
                                                     self.attributes)

        response = gconn.create_sharing_profile(self.parent_identifier,
                                                self.name,
                                                self.attributes)

        if isinstance(response, dict):
            self.identifier = response.get('identifier')

        return response


    def delete(self):
        """
        Deletes a connection group
        """
        if not self.identifier:
            return None

        gconn = self.gconn
        return gconn.delete_sharing_profile(self.identifier)



class CurrentConnections():
    """
    An object that holds connection groups, instances and sharing profiles
    """
    def __init__(self,
                 gconn: guacamole.session,
                 parent_identifier: str = 'ROOT'):

        self.gconn = gconn
        self.parent_identifier = parent_identifier
        self.tree = gconn.detail_connection_group_connections(parent_identifier)
        self.connections = self.extract_connections(self.tree)
        self.identifiers = [conn.identifier for conn in self.connections]
    
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

        if dictionary.get('type'):
            return ConnectionGroup(self.gconn,
                                    dictionary['name'],
                                    dictionary['parentIdentifier'],
                                    dictionary['type'],
                                    dictionary.get('attributes'),
                                    dictionary['identifier'])
        if dictionary.get('protocol'):
            return ConnectionInstance(self.gconn,
                                      dictionary['protocol'],
                                      dictionary['name'],
                                      dictionary['parentIdentifier'],
                                      dictionary.get('parameters'),
                                      dictionary.get('attributes'),
                                      dictionary['identifier'])
        if dictionary.get('primaryConnectionIdentifier'):
            return SharingProfile(self.gconn,
                                  dictionary['name'],
                                  dictionary['primaryConnectionIdentifier'],
                                  dictionary.get('parameters'),
                                  dictionary['identifier'])
        return None


class NewConnections():
    """
    An object that holds connection groups, instances and sharing profiles
    """
    def __init__(self,
                 gconn: guacamole.session,
                 oconn: openstack.connect,
                 conn_data: dict,
                 parent_identifier: str = 'ROOT'):

        self.gconn = gconn
        self.parent_identifier = parent_identifier
        self.oconn = oconn
        self.conn_data = conn_data
        self.connections = []

        for name, data in self.conn_data['groups'].items():
            count = data.get('count', 1)
            self.connections.extend([
                ConnectionGroup(self.gconn,
                                data.get('name', name).replace(
                                    r'%index%', str(index + 1)
                                ),
                                data.get('parentIdentifier', 'ROOT'),
                                data.get('type', 'ORGANIZATIONAL'),
                                data.get('attributes'),
                )
                for index in range(count)
            ])

        for name, data in self.conn_data['connections'].items():
            count = data.get('count', 1)
            self.connections.extend([
                ConnectionInstance(self.gconn,
                                    data.get('protocol', 'ssh'),
                                    data.get('name', name).replace(
                                        r'%index%', str(index + 1)
                                    ),
                                    data.get('parentIdentifier', 'ROOT'),
                                    data.get('parameters'),
                                    data.get('attributes'),
                )
                for index in range(count)
            ])

        for name, data in self.conn_data.get('sharing_profiles', {}).items():
            count = data.get('count', 1)
            self.connections.extend([
                SharingProfile(self.gconn,
                                data.get('name', name).replace(
                                    r'%index%', str(index + 1)
                                ),
                                data.get('parentIdentifier', 'ROOT'),
                                data.get('attributes'),
                )
                for index in range(count)
            ])



with open('clouds.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)['clouds']['guac']

with open('templates/guac.yaml', 'r', encoding='utf-8') as file:
    guac = yaml.safe_load(file)

session = guacamole.session(config['host'],
                            config['data_source'],
                            config['username'],
                            config['password'])

# conn_group = ConnectionGroup(session, 'group1', 'ROOT', 'ORGANIZATIONAL')
# print(conn_group)
# print(conn_group.create())
# time.sleep(1)
# conn = ConnectionInstance(session, 'ssh', 'ssh', conn_group.identifier)
# time.sleep(1)
# print(conn.create())
# time.sleep(1)
# share = SharingProfile(session, 'ssh', conn.identifier)
# time.sleep(1)
# print(share.create())
# time.sleep(10)
# print(conn_group.delete())

# tree = CurrentConnections(session, '1821')

# print(tree.connections[0] in tree.connections)
# print(tree.identifiers[0] in tree.identifiers)

new_data = NewConnections(session, None, guac)

print(new_data.connections)

# print(tree_data)
