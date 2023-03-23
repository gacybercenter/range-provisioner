from openstack import config, connect
from utils.load_template import load_template, load_global


# stack_name = "dev_system"


def search_stack():
    """Search if stack exists"""
    print(f"Openstack_Heat:  Searching for {stack_name}...")
    try:
        stack_exists = conn.search_stacks(name_or_id=stack_name)
        print(stack_exists)
    except:
        print("Stack not found")
    return(stack_exists)


def create_stack(conn, stack_name, template, parameters):
    """Create a new stack"""
    try:
        if parameters is None:
            conn.create_stack(
                name=stack_name,
                template_file=template,
                rollback=False,
            )
        else:
            conn.create_stack(
                name=stack_name,
                template_file=template,
                rollback=False,
                **parameters,
            )
        print(f"Openstack_Heat:  The stack {stack_name} has been created")
    except Exception as e:
        print(f"Openstack_Heat ERROR:  {e}")

def create_stack_wait(conn, stack_name, template, parameters):
    try:
        if parameters is None:
            conn.create_stack(
                name=stack_name,
                template_file=template,
                wait=True,
                rollback=False,
            )
        else:
            conn.create_stack(
                name=stack_name,
                template_file=template,
                rollback=False,
                wait=True,
                **parameters,
            )
        print(f"Openstack_Heat:  The stack {stack_name} has been created")
    except Exception as e:
        print(f"Openstack_Heat ERROR:  {e}") 

def delete_stack(stack_name):
    """Delete a deployed stack"""
    if search_stack(stack_name):
        conn.delete_stack(name_or_id=stack_name)
        print(f"Openstack_Heat:  The stack {stack_name} exists... deleting")
    else:
        print(f"Openstack_Heat ERROR:  The stack {stack_name} cannot be"
              " deleted, it doesn't exist")

def update_stack(conn, stack_name, template, parameters):
    """Update a deployed stack"""
    if search_stack(stack_name):
        print(f"Openstack_Heat:  The stack {stack_name} exists... updating")
        conn.update_stack(
            name_or_id=stack_name,
            template_file=template,
            rollback=False,
            wait=True,
            **parameters,
        )
    else:
        print(f"Openstack_Heat:  The stack {stack_name} cannot be updated,"
              " it doesn't exist")
