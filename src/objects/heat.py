"""
Heat Classes
"""
from time import sleep
from openstack.connection import Connection
from utils import msg_format


class HeatStack:
    """
    Stack Object for Heat

    Args:
        self.conn (self.connection): OpenStack self.connection
        name (str): Name of the stack
        template_file (str): Template file for the stack
        parameters (dict): Parameters for the stack
        debug (bool): Debug mode
    """

    def __init__(self,
                 conn: Connection,
                 name: str,
                 template_file: str | None = None,
                 parameters: dict | None = None,
                 debug: bool = False):

        self.conn = conn
        self.name = name
        self.template_file = template_file
        self.parameters = parameters
        self.debug = debug
        self.endpoint = 'Heat'
        self.stack = None

        self._search()

    def __hash__(self):
        """
        Hash function for the HeatStack object
        """
        return hash(
            tuple(sorted(vars(self)))
        )

    def __eq__(self, other):
        """
        Equality function for the HeatStack object
        """
        if not isinstance(other, self.__class__):
            return False

        return vars(self) == vars(other)

    def __str__(self):
        """
        String function for the HeatStack object
        """
        class_name = type(self).__name__
        output = f'{class_name}(\n'
        for key, value in self.__dict__.items():
            output += f'{key}: {value}\n'
        output += ')'
        return output

    def __repr__(self):
        """
        Representation function for the HeatStack object
        """
        return self.__str__()

    def create(self, delay: float = 0):
        """
        Creates the heat stack if it doesn't exist
        """

        if not self.template_file:
            msg_format.error_msg(f"Can't create stack. No template file specified.",
                                 self.endpoint)
            return None

        if self.stack:
            msg_format.error_msg(f"Can't create stack. '{self.name}' already exists.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Creating stack '{self.name}'...",
                               self.endpoint)
        if self.parameters is None:
            response = self.conn.create_stack(
                name=self.name,
                template_file=self.template_file,
                wait=True,
                rollback=False,
            )
        else:
            if 'name' in self.parameters.keys():
                self.name = self.parameters['name']

            response = self.conn.create_stack(
                name=self.name,
                template_file=self.template_file,
                wait=True,
                rollback=False,
                **self.parameters,
            )
        sleep(delay)

        self.stack = response
        msg_format.success_msg(f"Created stack '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(response,
                            self.endpoint,
                            self.debug)

        return response

    def delete(self, delay: float = 0):
        """
        Deletes the heat stack if it exists
        """

        if not self.stack:
            msg_format.error_msg(f"Stack '{self.name}' doesn't exist.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Deleting stack '{self.name}'...",
                               self.endpoint)

        response = self.conn.delete_stack(name_or_id=self.name,
                                     wait=True)
        sleep(delay)

        self.stack = None
        msg_format.success_msg(f"Deleted stack '{self.name}'",
                               self.endpoint)

        return response

    def update(self, delay: float = 0):
        """
        Updates the heat stack if it exists
        """

        if not self.template_file:
            msg_format.error_msg(f"Can't update stack. No template file specified.",
                                 self.endpoint)
            return None

        if not self.stack:
            msg_format.error_msg(f"Can't update stack '{self.name}' because it doesn't exist.",
                                 self.endpoint)
            return None

        msg_format.general_msg(f"Updating stack '{self.name}'...",
                               self.endpoint)
        if self.parameters is None:
            response = self.conn.update_stack(
                name_or_id=self.name,
                template_file=self.template_file,
                wait=True,
                rollback=False,
            )
        else:
            if 'name' in self.parameters.keys():
                self.name = self.parameters['name']

            response = self.conn.update_stack(
                name_or_id=self.name,
                template_file=self.template_file,
                wait=True,
                rollback=False,
                **self.parameters,
            )
        sleep(delay)

        self.stack = response
        msg_format.success_msg(f"Updated stack '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(response,
                            self.endpoint,
                            self.debug)

        return response

    def get_ip_addresses(self, delay: float = 0):
        """
        Returns the IP addresses of the server instances in the stack
        """

        ip_addresses = {}
        if not self.stack:
            msg_format.error_msg(f"Can't get stack IPs. '{self.name}'. doesn't exist.",
                                 self.endpoint)
            return ip_addresses

        msg_format.general_msg(f"Getting instance IPs from stack '{self.name}'...",
                               self.endpoint)

        instances = self.get_stack_instances(delay=delay)
        for instance in instances:
            server = self.conn.get_server(
                name_or_id=instance['physical_resource_id']
            )
            sleep(delay)
            hostname = server['public_v4'] if server['public_v4'] else server['private_v4']
            ip_addresses[server['name']] = hostname
            msg_format.general_msg(f"Found IP address '{hostname}' for instance '{server['name']}'",
                                   self.endpoint)
            msg_format.info_msg(server,
                                self.endpoint,
                                self.debug)

        msg_format.success_msg(f"Found all IPs in stack '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(ip_addresses,
                            self.endpoint,
                            self.debug)

        return ip_addresses

    def get_stack_instances(self, delay: float = 0):
        """
        Returns the server instances in the stack
        """


        instances = []
        if not self.stack:
            msg_format.error_msg(f"Can't get stack instances. '{self.name}'. doesn't exist.",
                                 self.endpoint)
            return instances

        msg_format.general_msg(f"Getting stack instances in '{self.name}'...",
                               self.endpoint)

        resources = self.conn.orchestration.resources(self.name)
        sleep(delay)
        for resource in resources:
            if resource.resource_type == 'OS::Nova::Server':
                instances.append(resource)
                msg_format.general_msg(f"Found instance '{resource['logical_resource_id']}'",
                                       self.endpoint)
                msg_format.info_msg(resource,
                                    self.endpoint,
                                    self.debug)
            elif resource.resource_type == 'OS::Heat::ResourceGroup':
                children = self.conn.orchestration.resources(resource.physical_resource_id)
                sleep(delay)
                for child in children:
                    if child.resource_type == 'OS::Nova::Server':
                        instances.append(child)
                        msg_format.general_msg(f"Found resource group instance '{resource['logical_resource_id']}'",
                                               self.endpoint)
                        msg_format.info_msg(resource,
                                            self.endpoint,
                                            self.debug)

        msg_format.general_msg(f"Found {len(instances)} stack instances in '{self.name}'",
                               self.endpoint)
        msg_format.info_msg(instances,
                            self.endpoint,
                            self.debug)

        return instances

    def _search(self, delay: float = 0):
        """
        Search for the heat stack in OpenStack
        """

        msg_format.general_msg(f"Searching for stack '{self.name}'...",
                               self.endpoint)
        result = self.conn.get_stack(name_or_id=self.name)
        sleep(delay)
        if result:
            msg_format.general_msg(f"Found stack '{self.name}'",
                                   self.endpoint)
            msg_format.info_msg(result,
                                self.endpoint,
                                self.debug)
            self.stack = result
            return True

        msg_format.general_msg(f"Didn't find stack '{self.name}'",
                               self.endpoint)
        self.stack = None
        return False
