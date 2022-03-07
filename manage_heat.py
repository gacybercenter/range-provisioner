import openstack
import constants
import yaml
import logging
import munch
from openstack.config import loader
from heatclient.client import Client

cloud = constants.CLOUD

tenant_id = constants.TENANT_ID
heat_user = constants.USER
password = constants.PASS
stack_descr = constants.STACK_DESCR
stack_num = constants.STACK_NUM
environment_name = constants.ENV_NAME
environment_template = constants.ENV_TEMPLATE
secgroup_template = constants.SECGROUP_TEMPLATE
sec_action = constants.SEC_ACTION
env_action = constants.ENV_ACTION

# openstack.enable_logging(debug=True)

config = loader.OpenStackConfig()
conn = openstack.connect(cloud=cloud)


def deploy_stack(stack_name, template, parameters):
    conn.create_stack(
        name=stack_name,
        template_file=template,
        rollback=False,
        wait=True,
        **parameters,
    )

    name = conn.search_stacks(name_or_id=stack_name)
    stack_munch = (name[0])
    print(f"The stack {stack_munch.stack_name} has been deployed with a status of {stack_munch.status}")


def update_stack(stack_name, template, parameters):
    conn.update_stack(
        name_or_id=stack_name,
        template_file=template,
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
    parameters = {}

    if sec_action == "create":
        sec_name = f"{environment_name}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Security group {stack} already exists")
        else:
            print(f"Stack {sec_name} secgroup stack is being created with {secgroup_template} template")
            deploy_stack(sec_name, secgroup_template, parameters)

    if sec_action == "update":
        sec_name = f"{environment_name}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Stack {sec_name} security group exists... deleting")
            update_stack(sec_name, secgroup_template, parameters)
        else:
            print(f"Security group {sec_name} can't be updated, it doesn't exist")

    if sec_action == "delete":
        sec_name = f"{environment_name}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Stack {sec_name} security group exists... deleting")
            delete_stack(sec_name)
        else:
            print(f"Security group {sec_name} can't be deleted, it doesn't exist")

    if env_action == "create":
        parameters = {
            "tenant_id" : tenant_id,
            "heat_user": heat_user,
            "password": password,
            "stack_descr": stack_descr,
            "stack_num": stack_num,
            }
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
                    print(f"Stack {stack_name} environment is being created with {environment_template} template")
                    deploy_stack(stack_name, environment_template, parameters)
        except Exception:
            print(f"An exception occurred for creation of stack {stack_name}")

    if env_action == "update":
        parameters = {
            "tenant_id" : tenant_id,
            "heat_user": heat_user,
            "password": password,
            "stack_descr": stack_descr,
            "stack_num": stack_num,
            }
        try:
            stack_exists = conn.search_stacks(name_or_id=stack_name)
            stack_munch = (stack_exists[0])
            if stack_munch.stack_name == stack_name:
                print(f"Stack {stack_name} exists... updating")
                update_stack(stack_name, environment_template, parameters)
        except:
            print(f"Stack {stack_name} can't be updated, it doesn't exist")

    if env_action == "delete":
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