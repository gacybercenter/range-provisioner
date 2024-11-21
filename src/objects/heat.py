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
                 template_file: str,
                 parameters: dict | None = None,
                 debug: bool = False):

        self.conn = conn
        self.name = name
        self.template_file = template_file
        self.parameters = parameters
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

    def create(self,
               wait: bool = True,
               delay: float = 0):
        """Create a new stack with the provided parameters."""

        response = self._create_stack(wait)
        sleep(delay)

        return response

    def delete(self,
               wait: bool = True,
               delay: float = 0):
        """Delete a new stack with the provided parameters."""

        response = self._delete_stack(wait)
        sleep(delay)

        return response

    def update(self,
               wait: bool = True,
               delay: float = 0):
        """Update a new stack with the provided parameters."""

        response = self._update_stack(wait)
        sleep(delay)

        return response

    def get_ip_addresses(self):
        """Get the IP address of the stack."""

        name = self.name
        endpoint = 'Heat'

        if not self.stack:
            msg_format.error_msg(f"Can't get stack IPs. '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Getting instance IPs from stack '{name}'",
                               endpoint)

        instances = self.get_stack_instances()
        ip_addresses = [
            {
                'name': instance['name'],
                'hostname': instance['public_v4'] if instance['public_v4'] else instance['private_v4']
            }
            for instance in instances
        ]

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

        if not self.stack:
            msg_format.error_msg(f"Can't get stack instances. '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Getting instances from stack '{name}'",
                               endpoint)

        resources = conn.orchestration.resources(name)
        instances = [
            resource
            for resource in resources
            if resource.resource_type == 'OS::Nova::Server'
        ]
        msg_format.success_msg(f"Found {len(instances)} instances in stack '{name}'",
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

    def _create_stack(self, wait: bool = True):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        template_file = self.template_file
        parameters = self.parameters
        endpoint = 'Heat'

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
                rollback=True,
            )
        else:
            if 'name' in parameters.keys():
                name = parameters['name']
                self.name = name

            response = conn.create_stack(
                name=name,
                template_file=template_file,
                wait=wait,
                rollback=True,
                **parameters,
            )

        self._search()
        msg_format.success_msg(f"Created stack '{name}'",
                               endpoint)
        msg_format.info_msg(response,
                            endpoint,
                            self.debug)

        return response

    def _delete_stack(self, wait: bool = True):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        endpoint = 'Heat'

        if not self.stack:
            msg_format.error_msg(f"Stack '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.error_msg(f"Can't delete stack. '{name}' doesn't exist.",
                             endpoint)
        response = conn.delete_stack(name_or_id=name,
                                     wait=wait)

        self.stack = None
        msg_format.success_msg(f"Deleted stack '{name}'",
                               endpoint)
        msg_format.info_msg(response,
                            endpoint,
                            self.debug)

        return response

    def _update_stack(self, wait: bool = True):
        """
        Default implementation for creating a stack
        """

        conn = self.conn
        name = self.name
        template_file = self.template_file
        parameters = self.parameters
        endpoint = 'Heat'

        if not self.stack:
            msg_format.error_msg(f"Can't update stack. '{name}' doesn't exist.",
                                 endpoint)
            return None

        msg_format.general_msg(f"Updating stack '{name}'",
                               endpoint)
        if parameters is None:
            response = conn.update_stack(
                name=name,
                template_file=template_file,
                wait=wait,
                rollback=True,
            )
        else:
            if 'name' in parameters.keys():
                name = parameters['name']
                self.name = name

            response = conn.update_stack(
                name=name,
                template_file=template_file,
                wait=wait,
                rollback=True,
                **parameters,
            )

        self._search()
        msg_format.success_msg(f"Updated stack '{name}'",
                               endpoint)
        msg_format.info_msg(response,
                            endpoint,
                            self.debug)

        return response

