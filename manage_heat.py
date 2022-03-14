from yaml import safe_load
from openstack import config, connect, enable_logging


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


def search_stack(stack_name):
    """Search if stack exists"""
    print(f"Openstack_Heat:  Searching for {stack_name}...")
    stack_exists = conn.search_stacks(name_or_id=stack_name)
    return(stack_exists)


def main():
    # Create main dictionary and load templates
    heat_dict = {}
    extra_params = {}
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)
    sec_params = load_template(secgroup_template)

    # Update main dictionary and update keys and values loaded from templates
    heat_dict.update({'num_stacks':
                     global_params['global']['num_users']})
    heat_dict.update({'main_action':
                     global_params['openstack']['main_action']})
    heat_dict.update({'main_stack_name':
                     f"{heat_params['parameters']['instance_id']['default']}.{global_params['global']['username_prefix']}"})
    heat_dict.update({'sec_action':
                     global_params['openstack']['sec_action']})
    heat_dict.update({'sec_stack_name':
                     sec_params['parameters']['name']['default']})
    heat_dict.update({'username':
                     heat_params['parameters']['username']['default']})
    heat_dict.update({'password':
                     heat_params['parameters']['password']['default']})

    # Create dynamic parameters dictionary
    for k, v in heat_params['parameters'].items():
        extra_params.update({f"{k}": v['default']})
    
    print(heat_dict['main_stack_name'])

    extra_params.update({'tenant_id': load_template('clouds.yaml')['clouds']['gcr']['auth']['project_id']})
    extra_params.update({'instance_id': heat_dict['main_stack_name']})

    # Security group template actions
    if heat_dict['sec_action'] == 'delete':
        delete_stack(heat_dict['sec_stack_name'])
    if heat_dict['sec_action'] == 'update':
        update_stack(heat_dict['sec_stack_name'], secgroup_template, None)
    if heat_dict['sec_action'] == 'create':
        create_stack(heat_dict['sec_stack_name'], secgroup_template, None)

    # Main template action for a given number of stacks based on globals
    #  template data
    for num in range(1, heat_dict['num_stacks']+1):
        heat_dict.update({'stack_num': num})
        extra_params.update({"instance_id": f'{heat_dict["main_stack_name"]}.{num}'})
        parameters = extra_params
        print(parameters)
        if heat_dict['main_action'] == 'delete':
            delete_stack(f'{heat_dict["main_stack_name"]}.{num}')
        if heat_dict['main_action'] == 'update':
            update_stack(f'{heat_dict["main_stack_name"]}.{num}',
                         main_template, parameters)
        if heat_dict['main_action'] == 'create':
            create_stack(f'{heat_dict["main_stack_name"]}.{num}',
                         main_template, parameters)


if __name__ == '__main__':
    print("***  Begin Heat management script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template(globals_template)['openstack']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    secgroup_template = f'{template_dir}/sec.yaml'
    config = config.loader.OpenStackConfig()
    conn = connect(cloud=load_template
                   (globals_template)['global']['cloud'])
    enable_logging(debug=load_template
                   (globals_template)['global']['debug'])
    main()
    print("\n*** End Heat management script  ***")
