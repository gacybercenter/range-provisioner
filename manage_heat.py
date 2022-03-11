import openstack
import constants
import yaml
import logging
import munch
from openstack.config import loader
from heatclient.client import Client

cloud = constants.CLOUD

tenant_id = constants.OSTACK_TENANT_ID
user = constants.OSTACK_INSTANCE_USERNAME
password = constants.OSTACK_INSTANCE_PW
instance_descr = constants.OSTACK_INSTANCE_DESCR
stack_num = constants.OSTACK_STACK_NUM
stack_descr = constants.OSTACK_STACK_DESCR
stack_template = constants.OSTACK_STACK_TEMPLATE
secgroup_template = constants.OSTACK_SEC_TEMPLATE
sec_action = constants.OSTACK_SEC_ACTION
stack_action = constants.OSTACK_STACK_ACTION

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
    print(f"Openstack_Heat:  The stack {stack_munch.stack_name} has been deployed with a status of {stack_munch.status}")


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
        sec_name = f"{stack_descr}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Openstack_Heat:  Security group {stack} already exists")
        else:
            print(f"Openstack_Heat:  Stack {sec_name} secgroup stack is being created with {secgroup_template} template")
            deploy_stack(sec_name, secgroup_template, parameters)

    if sec_action == "update":
        sec_name = f"{stack_descr}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Openstack_Heat:  Stack {sec_name} security group exists... deleting")
            update_stack(sec_name, secgroup_template, parameters)
        else:
            print(f"Openstack_Heat:  Security group {sec_name} can't be updated, it doesn't exist")

    if sec_action == "delete":
        sec_name = f"{stack_descr}.secgroups"
        stack_exists = conn.search_stacks(name_or_id=sec_name)
        if stack_exists:
            stack = stack_exists[0].name
            print(f"Openstack_Heat:  Stack {sec_name} security group exists... deleting")
            delete_stack(sec_name)
        else:
            print(f"Openstack_Heat:  Security group {sec_name} can't be deleted, it doesn't exist")

    if stack_action == "create":
        parameters = {
            "tenant_id" : tenant_id,
            "username": user,
            "password": password,
            "instance_descr": instance_descr,
            "stack_num": stack_num,
            }
        try:
            for number in range(stack_num):
                stack_name = f'{stack_descr}.{number+1}'
                parameters["stack_num"] = number+1
                stack_exists = conn.search_stacks(name_or_id=stack_name)
                if len(stack_exists) > 0:
                    stack_munch = (stack_exists[0])
                    if stack_munch.stack_name == stack_name:
                        print(f"Openstack_Heat:  Stack {stack_name} already exists")
                        stack_exists = True
                else:
                    print(f"Openstack_Heat:  Stack {stack_name} environment is being created with {stack_template} template")
                    deploy_stack(stack_name, stack_template, parameters)
        except Exception as e:
            # print(f"An exception occurred for creation of stack {stack_name}")
            print(e)

    if stack_action == "update":
        parameters = {
            "tenant_id" : tenant_id,
            "username": user,
            "password": password,
            "instance_descr": instance_descr,
            "stack_num": stack_num,
            }
        try:
            stack_exists = conn.search_stacks(name_or_id=stack_name)
            stack_munch = (stack_exists[0])
            if stack_munch.stack_name == stack_name:
                print(f"Openstack_Heat:  Stack {stack_name} exists... updating")
                update_stack(stack_name, stack_template, parameters)
        except:
            print(f"Openstack_Heat:  Stack {stack_name} can't be updated, it doesn't exist")

    if stack_action == "delete":
        for number in range(stack_num):
            stack_name = f'{stack_descr}.{number+1}'
            parameters["stack_num"] = number+1
            try:
                stack_exists = conn.search_stacks(name_or_id=stack_name)
                stack_munch = (stack_exists[0])
                if stack_munch.stack_name == stack_name:
                    print(f"Openstack_Heat:  Stack {stack_name} exists... deleting")
                    delete_stack(stack_name)
            except:
                print(f"Openstack_Heat:  Stack {stack_name} can't be deleted, it doesn't exist")
            


if __name__ == '__main__':
    main()