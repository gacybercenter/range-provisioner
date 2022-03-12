import openstack
import constants
import yaml
import logging
import munch
from openstack.config import loader
from heatclient.client import Client

# Specifies cloud params in clouds.yaml


# Template dir/params
template_dir = './templates/'
main_template = f'{template_dir}main.yaml'
secgroup_template = f'{template_dir}sec.yaml'
globals_template = 'globals.yaml'



# tenant_id = constants.OSTACK_TENANT_ID
# user = constants.OSTACK_INSTANCE_USERNAME
# password = constants.OSTACK_INSTANCE_PW
instance_descr = constants.OSTACK_INSTANCE_DESCR
stack_num = constants.OSTACK_STACK_NUM
stack_descr = constants.OSTACK_STACK_DESCR
# stack_template = 'main.yaml'
# secgroup_template = constants.OSTACK_SEC_TEMPLATE
sec_action = constants.OSTACK_SEC_ACTION
stack_action = constants.OSTACK_STACK_ACTION

# openstack.enable_logging(debug=True)

def load_template(template):
    with open(template, 'r') as file:
        params_template = yaml.safe_load(file)
    return params_template

def update_stack(stack_name, template, parameters):
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
        print(f"Openstack_Heat:  The stack {stack_name} cannot be updated, it doesn't exist")

def delete_stack(stack_name):
    if search_stack(stack_name):
        print(f"Openstack_Heat:  The stack {stack_name} exists... deleting")
        conn.delete_stack(name_or_id=stack_name)
    else:
        print(f"Openstack_Heat ERROR:  The stack {stack_name} cannot be deleted, it doesn't exist")


def create_stack(stack_name, template, parameters):
    if search_stack(stack_name):
        print(f"Openstack_Heat ERROR:  The stack {stack_name} already exists")
    else:
        conn.create_stack(
            name=stack_name,
            template_file=template,
            rollback=False,
            **parameters,
        )
        print(f"Openstack_Heat:  The stack {stack_name} is creating...")

def search_stack(stack_name):
    print(f'Openstack_Heat:  searching for {stack_name}...')
    stack_exists = conn.search_stacks(name_or_id=stack_name)
    return(stack_exists)



def main():
    heat_dict = {}
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)
    sec_params = load_template(secgroup_template)

    heat_dict.update({'num_stacks': global_params['global']['num_users']})
    heat_dict.update({'main_action': global_params['openstack']['main_action']})
    heat_dict.update({'main_stack_name': heat_params['parameters']['name']['default']})
    heat_dict.update({'sec_action': global_params['openstack']['sec_action']})
    heat_dict.update({'sec_stack_name': sec_params['parameters']['name']['default']})
    heat_dict.update({'tenant_id': load_template('clouds.yaml')['clouds']['gcr']['auth']['project_id']})
    heat_dict.update({'username': heat_params['parameters']['username']['default']})
    heat_dict.update({'password': heat_params['parameters']['password']['default']})
    
    
    if heat_dict['sec_action'] == "delete":
        delete_stack(heat_dict['sec_stack_name'])
    if heat_dict['sec_action'] == 'update':
        update_stack(heat_dict['sec_stack_name'], secgroup_template, None)

    for num in range(1, heat_dict['num_stacks']+1):
        heat_dict.update({'stack_num': num})
        parameters = {
            "tenant_id" : heat_dict['tenant_id'],
            "stack_num" : heat_dict['stack_num'],
        }

        if heat_dict['main_action'] == 'delete':
            delete_stack(f'{heat_dict["main_stack_name"]}.{num}')
        if heat_dict['main_action'] == 'update':
            update_stack(f'{heat_dict["main_stack_name"]}.{num}', main_template, parameters)
        if heat_dict['main_action'] == 'create':
            create_stack(f'{heat_dict["main_stack_name"]}.{num}', main_template, parameters)            







        # if conn.search_stacks(name_or_id=heat_dict['sec_stack_name']):
        #     print(f"Openstack_Heat:  Stack {heat_dict['sec_stack_name']} security group exists... deleting")
        # else:
        #     print(f"Openstack_Heat:  ERROR: Security group {heat_dict['sec_stack_name']} doesn't exist")
    # if heat_dict['main_action'] == "delete":
    #     if conn.search
    
    
    # if heat_dict['sec_action'] == "update":

    # if heat_dict['sec_action'] == "create":


    # if heat_dict['main_action'] == "delete":
    # if heat_dict['main_action'] == "update":
    # if heat_dict['main_action'] == "create":




    

    


    

    # if sec_action == "create":
    #     sec_name = f"{stack_descr}.secgroups"
    #     stack_exists = conn.search_stacks(name_or_id=sec_name)
    #     if stack_exists:
    #         stack = stack_exists[0].name
    #         print(f"Openstack_Heat:  Security group {stack} already exists")
    #     else:
    #         print(f"Openstack_Heat:  Stack {sec_name} secgroup stack is being created with {secgroup_template} template")
    #         deploy_stack(sec_name, secgroup_template, parameters)

    # if sec_action == "update":
    #     sec_name = f"{stack_descr}.secgroups"
    #     stack_exists = conn.search_stacks(name_or_id=sec_name)
    #     if stack_exists:
    #         stack = stack_exists[0].name
    #         print(f"Openstack_Heat:  Stack {sec_name} security group exists... deleting")
    #         update_stack(sec_name, secgroup_template, parameters)
    #     else:
    #         print(f"Openstack_Heat:  Security group {sec_name} can't be updated, it doesn't exist")

    # if sec_action == "delete":
    #     sec_name = f"{stack_descr}.secgroups"
    #     stack_exists = conn.search_stacks(name_or_id=sec_name)
    #     if stack_exists:
    #         stack = stack_exists[0].name
    #         print(f"Openstack_Heat:  Stack {sec_name} security group exists... deleting")
    #         delete_stack(sec_name)
    #     else:
    #         print(f"Openstack_Heat:  Security group {sec_name} can't be deleted, it doesn't exist")

    # if stack_action == "create":
    #     parameters = {
    #         "tenant_id" : tenant_id,
    #         "username": user,
    #         "password": password,
    #         "instance_descr": instance_descr,
    #         "stack_num": stack_num,
    #         }
    #     try:
    #         for number in range(stack_num):
    #             stack_name = f'{stack_descr}.{number+1}'
    #             parameters["stack_num"] = number+1
    #             stack_exists = conn.search_stacks(name_or_id=stack_name)
    #             if len(stack_exists) > 0:
    #                 stack_munch = (stack_exists[0])
    #                 if stack_munch.stack_name == stack_name:
    #                     print(f"Openstack_Heat:  Stack {stack_name} already exists")
    #                     stack_exists = True
    #             else:
    #                 print(f"Openstack_Heat:  Stack {stack_name} environment is being created with {stack_template} template")
    #                 deploy_stack(stack_name, stack_template, parameters)
    #     except Exception as e:
    #         # print(f"An exception occurred for creation of stack {stack_name}")
    #         print(e)

    # if stack_action == "update":
    #     parameters = {
    #         "tenant_id" : tenant_id,
    #         "username": user,
    #         "password": password,
    #         "instance_descr": instance_descr,
    #         "stack_num": stack_num,
    #         }
    #     try:
    #         stack_exists = conn.search_stacks(name_or_id=stack_name)
    #         stack_munch = (stack_exists[0])
    #         if stack_munch.stack_name == stack_name:
    #             print(f"Openstack_Heat:  Stack {stack_name} exists... updating")
    #             update_stack(stack_name, stack_template, parameters)
    #     except:
    #         print(f"Openstack_Heat:  Stack {stack_name} can't be updated, it doesn't exist")

    # if stack_action == "delete":
    #     for number in range(stack_num):
    #         stack_name = f'{stack_descr}.{number+1}'
    #         parameters["stack_num"] = number+1
    #         try:
    #             stack_exists = conn.search_stacks(name_or_id=stack_name)
    #             stack_munch = (stack_exists[0])
    #             if stack_munch.stack_name == stack_name:
    #                 print(f"Openstack_Heat:  Stack {stack_name} exists... deleting")
    #                 delete_stack(stack_name)
    #         except:
    #             print(f"Openstack_Heat:  Stack {stack_name} can't be deleted, it doesn't exist")
            


if __name__ == '__main__':
    cloud = load_template('globals.yaml')['global']['cloud']
    config = loader.OpenStackConfig()
    conn = openstack.connect(cloud=cloud)
    main()