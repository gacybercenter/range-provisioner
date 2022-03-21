import constants
from json import loads
from yaml import safe_load
from openstack import config, connect, enable_logging

guac_admin = constants.GUAC_ADMIN
guac_password = constants.GUAC_ADMIN_PASS
guac_user_password = constants.GUAC_USER_PASSWORD

def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template

def get_ostack_instances():
    """Obtain openstack instance names and public addresses"""
    instances = [instance.name
        for instance in conn.list_servers()
        ]
    return instances

def main():
    # Load templates
    global_params = load_template(globals_template)

    # Create dictionaries
    global_dict = ([v for k, v in global_params.items() if k == "global"])[0]

    if global_params['heat']['remove_sec'] == True:
        for instance in get_ostack_instances():
            conn.remove_server_security_groups(instance, global_params['heat']['sec_group_name'])
    else:
        print("not enabled")

if __name__ == '__main__':
    print("***  Begin secgroup modification script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template(globals_template)['heat']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    config = config.loader.OpenStackConfig()
    conn = connect(cloud=load_template(
        globals_template)['global']['cloud'])
    enable_logging(debug=load_template(
        globals_template)['global']['debug'])
    main()
    print("\n*** End secgroup modification script  ***")