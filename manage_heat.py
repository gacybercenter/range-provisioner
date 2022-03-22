from yaml import safe_load
from openstack import config, connect, enable_logging
import time


def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


def update_stack(stack_name, template, parameters):
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


def delete_stack(stack_name):
    """Delete a deployed stack"""
    if search_stack(stack_name):
        conn.delete_stack(name_or_id=stack_name)
        print(f"Openstack_Heat:  The stack {stack_name} exists... deleting")
    else:
        print(f"Openstack_Heat ERROR:  The stack {stack_name} cannot be"
              " deleted, it doesn't exist")


def create_stack(stack_name, template, parameters):
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

def create_stack_wait(stack_name, template, parameters):
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


def search_stack(stack_name):
    """Search if stack exists"""
    print(f"Openstack_Heat:  Searching for {stack_name}...")
    stack_exists = conn.search_stacks(name_or_id=stack_name)
    return(stack_exists)


def main():
    # Load templates
    extra_params = {}
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)
    sec_params = load_template(secgroup_template)

    # Create dictionaries
    extra_params_dict = {}
    global_dict = ([v for k, v in global_params.items() if k == "global"])[0]
    heat_global_dict = ([v for k, v in global_params.items() if k == "heat"])[0]
    heat_params_items = ([v for k, v in heat_params.items() if k == "parameters"])[0]
    heat_params_keys = ([k for k in heat_params_items])
    heat_params_values = ([v['default'] for k, v in heat_params_items.items()])
    heat_param_dict = dict(zip(heat_params_keys, heat_params_values))

    # Update params dictionary
    heat_param_dict.update({'tenant_id': load_template('clouds.yaml')['clouds']['gcr']['auth']['project_id']})
    heat_params_items.update({'instance_id':
                     f"{heat_params_items['instance_id']['default']}"
                     f".{global_dict['username_prefix']}"})

    # Check global for create_all value
    if global_dict['create_all'] is True:
        heat_global_dict.update(
            {
                'main_action': 'create',
                # 'sec_action': 'create',
            }
            )
    elif global_dict['create_all'] is False:
                heat_global_dict.update(
            {
                'main_action': 'delete',
                # 'sec_action': 'delete',
            }
            )
    elif heat_global_dict['sec_action'] == 'delete':
        delete_stack(sec_params['parameters']['name']['default'])
    elif heat_global_dict['sec_action'] == 'update':
        update_stack(sec_params['parameters']['name']['default'], secgroup_template, None)
    elif heat_global_dict['sec_action'] == 'create':
        create_stack(sec_params['parameters']['name']['default'], secgroup_template, None)
    else:
        pass

    # Main template action for a given number of stacks based on globals
    # template data
    for num in range(1, global_dict['num_users']+1):
        heat_param_dict.update({'instance_id': f"{heat_params_items['instance_id']}.{num}"})
        if heat_global_dict['main_action'] == 'delete':
            delete_stack(f'{heat_param_dict["instance_id"]}')
        if heat_global_dict['main_action'] == 'update':
            update_stack(f'{heat_param_dict["instance_id"]}',
                         main_template, heat_param_dict)
        if heat_global_dict['main_action'] == 'create':
            if num == global_dict['num_users']:
                create_stack_wait(f'{heat_param_dict["instance_id"]}',
                         main_template, heat_param_dict)
            else:
                create_stack(f'{heat_param_dict["instance_id"]}',
                            main_template, heat_param_dict)

if __name__ == '__main__':
    print("***  Begin Heat management script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template(globals_template)['heat']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    secgroup_template = f'{template_dir}/sec.yaml'
    config = config.loader.OpenStackConfig()
    conn = connect(cloud=load_template
                   (globals_template)['global']['cloud'])
    enable_logging(debug=load_template
                   (globals_template)['global']['debug'])
    main()
    print("\n*** End Heat management script  ***")
