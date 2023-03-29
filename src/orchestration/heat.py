
from utils.msg_format import error_msg, info_msg, success_msg, general_msg


def provision(conn, stack, template, parameters, last_stack=False, update_stack=False, debug=False):
    """Provision container and upload assets"""
    try:
        if update_stack:
            update(conn, stack, template, parameters, last_stack, debug)
        else:
            create(conn, stack, template, parameters, last_stack, debug)

    except Exception as e:
        error_msg(e)


def deprovision(conn, stack, wait, debug=False):
    """Deprovision container and delete assets"""
    try:
        delete(conn, stack, wait, debug)
    except Exception as e:
        error_msg(e)


def search(conn, stack_name, debug=False):
    """Search for a stack and return the stack if it exists."""
    try:
        general_msg(f"Searching for stack... {stack_name}")
        result = conn.search_stacks(name_or_id=stack_name)
        if result:
            success_msg(f"{stack_name} stack exists")
            return result
        general_msg(f"{stack_name} stack doesn't exist")
        return None
    except Exception as e:
        error_msg(e)


def create(conn, stack, template, parameters, last_stack=False, debug=False):
    """Create a new stack with the provided parameters."""
    try:
        exists = search(conn, stack, debug)
        if exists:
            error_msg(f"The stack {stack} already exists")
            return None
        else:
            general_msg(f"Creating stack {stack}")
            if parameters is None:
                conn.create_stack(
                    name=stack,
                    template_file=template,
                    wait=last_stack,
                    rollback=False,
                )
            else:
                conn.create_stack(
                    name=stack,
                    template_file=template,
                    rollback=False,
                    wait=last_stack,
                    **parameters,
                )
            success_msg(f"The stack has been created:  {stack}")
    except Exception as e:
        error_msg(e)

def update(conn, stack, template, parameters, last_stack=False, debug=False):
    """Update a deployed stack"""
    try:
        exists = search(conn, stack, debug)
        if exists:
            general_msg(f"Updating stack {stack}")
            stack_update = conn.update_stack(
                name_or_id=stack,
                template_file=template,
                rollback=False,
                wait=last_stack,
                **parameters,
            )
            if stack_update:
                success_msg(f"The stack {stack} has been updated")
                return stack_update
            else:
                error_msg(f"The stack {stack} does not exists")
                return None
        else:
            error_msg(f"The stack {stack} cannot be updated, it doesn't exist")
    except Exception as e:
        error_msg(e)

def delete(conn, stack, wait, debug=False):
    """Delete a deployed stack"""
    try:
        exists = search(conn, stack, debug)
        if exists:
            general_msg(f"Deleting stack {stack}")
            conn.delete_stack(name_or_id=stack, wait=wait)
            success_msg(f"The stack {stack} has been deleted")
        else:
            error_msg(f"The stack {stack} cannot be deleted, it doesn't exist")
    except Exception as e:
        error_msg(e)