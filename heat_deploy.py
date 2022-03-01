import openstack
import constants
import yaml
import logging
import munch
from openstack.config import loader
from heatclient.client import Client

tenant_id = constants.TENANT_ID
heat_user = constants.USER
password = constants.PASS

# openstack.enable_logging(debug=True)
template_file = "./templates/test.yaml"

config = loader.OpenStackConfig()
conn = openstack.connect()

stack_name = "test_provision_stack2"

parameters = {
    "tenant_id" : tenant_id,
    "heat_user": heat_user,
    "password": password,
    }


def deploy_stack(stack_name):
    conn.create_stack(
        name=stack_name,
        template_file=template_file,
        rollback=False,
        wait=True,
        **parameters,
    )

    name = conn.search_stacks(name_or_id=stack_name)
    stack_munch = (name[0])
    print(f"The stack {stack_munch.stack_name} has been deployed with a status of {stack_munch.status}")


def update_stack(stack_name):
    conn.update_stack(
        name_or_id=stack_name,
        template_file=template_file,
        rollback=False,
        wait=True,
        **parameters,
    )

def delete_stack(stack_name):
    conn.delete_stack(
        name_or_id=stack_name,
        wait=True,
    )


def main():

    if constants.EVENT_ACTION == "create":
        try:
            stack_exists = conn.search_stacks(name_or_id=stack_name)
            stack_munch = (stack_exists[0])
            if stack_munch.stack_name == stack_name:
                print(f"Stack {stack_name} already exists")
        except:
            print(f"Stack {stack_name} is being created")
            deploy_stack(stack_name)
    elif constants.EVENT_ACTION == "update":
        try:
            stack_exists = conn.search_stacks(name_or_id=stack_name)
            stack_munch = (stack_exists[0])
            if stack_munch.stack_name == stack_name:
                print(f"Stack {stack_name} exists... updating")
                update_stack(stack_name)
        except:
            print(f"Stack {stack_name} can't be updated, it doesn't exist")
    elif constants.EVENT_ACTION == "delete":
        try:
            stack_exists = conn.search_stacks(name_or_id=stack_name)
            stack_munch = (stack_exists[0])
            if stack_munch.stack_name == stack_name:
                print(f"Stack {stack_name} exists... deleting")
            delete_stack(stack_name)
        except:
            print(f"Stack {stack_name} can't be deleted, it doesn't exist")
            


if __name__ == '__main__':
    main()