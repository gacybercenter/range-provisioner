"""
Contains all the main functions for provisioning Heat
"""
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn: object,
              stack: str,
              template: str,
              parameters: dict,
              last_stack=False,
              update_stack=False,
              debug=False) -> None:
    """Provision container and upload assets"""

    if update_stack:
        update(conn,
               stack,
               template,
               parameters,
               last_stack,
               debug)
    else:
        create(conn,
               stack,
               template,
               parameters,
               last_stack,
               debug)


def deprovision(conn: object,
                stack: str,
                wait: bool,
                debug=False) -> None:
    """Deprovision container and delete assets"""

    delete(conn,
           stack,
           wait,
           debug)


def search(conn: object,
           stack_name: str,
           debug=False) -> list | None:
    """Search for a stack and return the stack if it exists."""

    general_msg(f"Heat:  Searching for stack... {stack_name}")
    result = conn.search_stacks(name_or_id=stack_name)
    if result:
        success_msg(f"Heat:  {stack_name} stack exists")
        info_msg(result, debug)
        return result
    general_msg(f"Heat:  {stack_name} stack doesn't exist")
    return None


def create(conn: object,
           stack: str,
           template: str,
           parameters: dict,
           last_stack=False,
           debug=False) -> None:
    """Create a new stack with the provided parameters."""

    exists = search(conn,
                    stack,
                    debug)
    if exists:
        error_msg(f"Heat:  The stack '{stack}' already exists")
        return None

    general_msg(f"Heat:  Creating stack '{stack}'")
    if parameters is None:
        conn.create_stack(
            name=stack,
            template_file=template,
            wait=last_stack,
            rollback=False,
        )
    else:
        if 'name' in parameters.keys():
            conn.create_stack(
                template_file=template,
                rollback=False,
                wait=last_stack,
                **parameters,
            )
        else:
            conn.create_stack(
                name=stack,
                template_file=template,
                rollback=False,
                wait=last_stack,
                **parameters,
            )
    success_msg(f"Heat:  Created '{stack}'")


def update(conn: object,
           stack: str,
           template: str,
           parameters: dict,
           last_stack=False,
           debug=False) -> None:
    """Update a deployed stack"""

    exists = search(conn, stack, debug)
    if exists:
        general_msg(f"Heat:  Updating stack '{stack}'")
        if parameters is None:
            conn.update_stack(
                name_or_id=stack,
                template_file=template,
                wait=last_stack,
                rollback=False,
            )
        else:
            conn.update_stack(
                name_or_id=stack,
                template_file=template,
                rollback=False,
                wait=last_stack,
                **parameters,
            )
        success_msg(f"Heat:  '{stack}' has been updated")
    else:
        error_msg(f"Heat:  '{stack}' cannot be updated, it doesn't exist")


def delete(conn: object,
           stack: str,
           wait: bool,
           debug=False) -> None:
    """Delete a deployed stack"""

    exists = search(conn, stack, debug)
    if exists:
        general_msg(f"Heat:  Deleting stack '{stack}'")
        conn.delete_stack(name_or_id=stack, wait=wait)
        success_msg(f"Heat:  The stack '{stack}' has been deleted")
    else:
        error_msg(
            f"Heat:  The stack '{stack}' cannot be deleted, it doesn't exist")


def get_ostack_instances(conn: object,
                         groups: list,
                         debug=False) -> list:
    """
    Obtain openstack instance names and addresses

    Parameters:
        conn (object): The connection object for accessing the openstack instance.
        groups (list): The list of groups to search for
        debug (bool, optional): A flag indicating whether to enable debug mode.
                                Defaults to False.

    Returns:
        list: A list of dictionaries containing the instance names and addresses.
            Each dictionary has the following keys:
                - name (str): The name of the instance.
                - public_v4 (str): The public IPv4 address of the instance.
                - private_v4 (str): The private IPv4 address of the instance.
    """
    instances = [
        {
            'name': instance['name'],
            'hostname': instance['public_v4'] if instance['public_v4'] else instance['private_v4']
        }
        for instance in conn.list_servers(False)
        if instance['name'].split('.')[0] in groups
    ]

    general_msg(f"Heat:  Retrieved stack instances in {groups}")
    info_msg(instances, debug)
    return instances
