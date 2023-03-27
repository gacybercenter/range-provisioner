
from utils.load_template import load_template, load_global
from utils.msg_format import error_msg, info_msg, success_msg


# stack = "dev_system"

def search_stack(conn, stack):
    """
    Search for a stack and return the stack if it exists.

    Args:
        stack (str): The name or ID of the stack to search.

    Returns:
        list: A list containing the stack(s) matching the given name or ID, or an empty list if no stack is found.
    """

    info_msg(f"Searching for stack:  {stack}")
    exists = conn.search_stacks(name_or_id=stack)
    try:
        if exists:
            success_msg(stack)
        else:
            error_msg(f"Stack not found:  {stack}")
    except Exception as e:
        error_msg(e) 
    return(exists)


def create_stack(conn, stack, template, parameters):
    """
    Create a new stack with the provided parameters.

    Args:
        stack (str): The name of the new stack to create.
        template (str): The path to the YAML template file.
        parameters (dict): A dictionary containing the parameters for the stack creation.
    """
    try:
        if parameters is None:
            conn.create_stack(
                name=stack,
                template_file=template,
                rollback=False,
            )
        else:
            conn.create_stack(
                name=stack,
                template_file=template,
                rollback=False,
                **parameters,
            )
        success_msg(f"The stack has been created:  {stack}")
    except Exception as e:
        error_msg(e)

def create_stack_wait(conn, stack, template, parameters):
    try:
        if parameters is None:
            conn.create_stack(
                name=stack,
                template_file=template,
                wait=True,
                rollback=False,
            )
        else:
            conn.create_stack(
                name=stack,
                template_file=template,
                rollback=False,
                wait=True,
                **parameters,
            )
        print(f"Openstack_Heat:  The stack {stack} has been created")
    except Exception as e:
        print(f"Openstack_Heat ERROR:  {e}") 

def delete_stack(stack):
    """Delete a deployed stack"""
    if search_stack(stack):
        conn.delete_stack(name_or_id=stack)
        print(f"Openstack_Heat:  The stack {stack} exists... deleting")
    else:
        print(f"Openstack_Heat ERROR:  The stack {stack} cannot be"
              " deleted, it doesn't exist")

def update_stack(conn, stack, template, parameters):
    """Update a deployed stack"""
    if search_stack(stack):
        print(f"Openstack_Heat:  The stack {stack} exists... updating")
        conn.update_stack(
            name_or_id=stack,
            template_file=template,
            rollback=False,
            wait=True,
            **parameters,
        )
    else:
        print(f"Openstack_Heat:  The stack {stack} cannot be updated,"
              " it doesn't exist")
