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
stack_descr = constants.STACK_DESCR
stack_num = constants.STACK_NUM
environment_name = constants.ENV_NAME

# openstack.enable_logging(debug=True)
template_file = "./templates/sec_plus_demo.yaml"

config = loader.OpenStackConfig()
conn = openstack.connect()

parameters = {
    "tenant_id" : tenant_id,
    "heat_user": heat_user,
    "password": password,
    "stack_descr": stack_descr,
    "stack_num": stack_num,
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
            for number in range(1, stack_num):
                stack_name = f'{environment_name}.{number}'
                parameters["stack_num"] = number
                stack_exists = conn.search_stacks(name_or_id=stack_name)
                if len(stack_exists) > 0:
                    stack_munch = (stack_exists[0])
                    if stack_munch.stack_name == stack_name:
                        print(f"Stack {stack_name} already exists")
                        stack_exists = True
                else:
                    print(f"Stack {stack_name} environment is being created with {template_file} template")
                    deploy_stack(stack_name)
        except Exception:
            print(f"An exception occurred for creation of stack {stack_name}")

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
        for number in range(1, stack_num):
            stack_name = f'{environment_name}.{number}'
            parameters["stack_num"] = number
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