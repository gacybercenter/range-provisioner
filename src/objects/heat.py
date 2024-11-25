"""
Connection Classes
"""
from time import sleep
from typing import Dict, Any, List
from openstack.connection import Connection
from utils import msg_format


class HeatStack:
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
                 template_file: str | None = None,
                 parameters: dict | None = None,
                 wait: bool = True,
                 debug: bool = False):

        self.conn = conn
        self.name = name
        self.template_file = template_file
        self.parameters = parameters
        self.wait = wait
        self.debug = debug
        self.stack = None

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

    def create(self):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        template_file = self.template_file
        parameters = self.parameters
        wait = self.wait
        endpoint = 'Heat'

        if not template_file:
            msg_format.error_msg(f"Can't create stack. No template file specified.",
                                 endpoint)
            return None

        if self.stack:
            msg_format.error_msg(f"Can't create stack. '{name}' already exists.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Creating stack '{name}'",
                               endpoint)
        if parameters is None:
            response = conn.create_stack(
                name=name,
                template_file=template_file,
                wait=wait,
                rollback=False,
            )
        else:
            if 'name' in parameters.keys():
                name = parameters['name']
                self.name = name

            response = conn.create_stack(
                name=name,
                template_file=template_file,
                wait=wait,
                rollback=False,
                **parameters,
            )

        self.stack = response
        msg_format.success_msg(f"Created stack '{name}'",
                               endpoint)
        msg_format.info_msg(response,
                            endpoint,
                            self.debug)

        return response

    def delete(self):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        wait = self.wait
        endpoint = 'Heat'

        if not self.stack:
            msg_format.error_msg(f"Stack '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Deleting stack '{name}'",
                               endpoint)

        response = conn.delete_stack(name_or_id=name,
                                     wait=wait)

        self.stack = None
        msg_format.success_msg(f"Deleted stack '{name}'",
                               endpoint)

        return response

    def update(self):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        template_file = self.template_file
        parameters = self.parameters
        wait = self.wait
        endpoint = 'Heat'

        if not template_file:
            msg_format.error_msg(f"Can't update stack. No template file specified.",
                                 endpoint)
            return None

        if not self.stack:
            msg_format.error_msg(f"Can't update stack. '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Updating stack '{name}'",
                               endpoint)
        if parameters is None:
            response = conn.update_stack(
                name_or_id=name,
                template_file=template_file,
                wait=wait,
                rollback=False,
            )
        else:
            if 'name' in parameters.keys():
                name = parameters['name']
                self.name = name

            response = conn.update_stack(
                name_or_id=name,
                template_file=template_file,
                wait=wait,
                rollback=False,
                **parameters,
            )

        self.stack = response
        msg_format.success_msg(f"Updated stack '{name}'",
                               endpoint)
        msg_format.info_msg(response,
                            endpoint,
                            self.debug)

        return response

    def get_ip_addresses(self):
        """Get the IP address of the stack."""

        name = self.name
        endpoint = 'Heat'
        ip_addresses = {}

        if not self.stack:
            msg_format.error_msg(f"Can't get stack IPs. '{name}' doesn't exist.",
                                 endpoint)
            return ip_addresses

        msg_format.general_msg(f"Getting instance IPs from stack '{name}'",
                               endpoint)

        instances = self.get_stack_instances()
        for instance in instances:
            server = self.conn.search_servers(
                name_or_id=instance['physical_resource_id']
            )[0]
            hostname = server['public_v4'] if server['public_v4'] else server['private_v4']
            ip_addresses[server['name']] = hostname
            msg_format.general_msg(f"Found IP address '{hostname}' for instance '{server['name']}'",
                                   endpoint)
            msg_format.info_msg(server,
                                endpoint,
                                self.debug)

        msg_format.success_msg(f"Found all IPs in stack '{name}'",
                               endpoint)
        msg_format.info_msg(ip_addresses,
                            endpoint,
                            self.debug)

        return ip_addresses

    def get_stack_instances(self):
        """Get the server instances in the stack."""

        conn = self.conn
        name = self.name
        endpoint = 'Heat'
        instances = []

        if not self.stack:
            msg_format.error_msg(f"Can't get stack instances. '{name}' doesn't exist.",
                                 endpoint)
            return instances

        msg_format.general_msg(f"Getting stack instances from stack '{name}'",
                               endpoint)

        resources = conn.orchestration.resources(name)
        for resource in resources:
            if resource.resource_type == 'OS::Nova::Server':
                instances.append(resource)
                msg_format.general_msg(f"Found stack instance '{resource['logical_resource_id']}'",
                                       endpoint)
                msg_format.info_msg(resource,
                                    endpoint,
                                    self.debug)
            elif resource.resource_type == 'OS::Heat::ResourceGroup':
                children = conn.orchestration.resources(resource.physical_resource_id)
                for child in children:
                    if child.resource_type == 'OS::Nova::Server':
                        instances.append(child)
                        msg_format.general_msg(f"Found stack instance resource group '{resource['logical_resource_id']}'",
                                               endpoint)
                        msg_format.info_msg(resource,
                                            endpoint,
                                            self.debug)

        msg_format.general_msg(f"Found {len(instances)} instances in stack '{name}'",
                               endpoint)
        msg_format.info_msg(instances,
                            endpoint,
                            self.debug)

        return instances

    def _search(self):
        """Search for a stack and return the stack if it exists."""

        conn = self.conn
        name = self.name
        debug = self.debug
        endpoint = 'Heat'

        msg_format.general_msg(f"Searching for stack '{name}'...",
                               endpoint)
        result = conn.get_stack(name_or_id=name)
        if result:
            msg_format.general_msg(f"Found stack '{name}'",
                                   endpoint)
            msg_format.info_msg(result,
                                endpoint,
                                debug)
            self.stack = result
            return True

        msg_format.general_msg(f"Didn't find stack '{name}'",
                               endpoint)
        self.stack = None
        return False
