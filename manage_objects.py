import openstack
from os import walk
from os.path import join
from yaml import safe_load
from openstack.config import loader


def load_template(template):
    """Load templates"""
    with open(template, 'r') as file:
        params_template = safe_load(file)
    return params_template


def create_container(container_name):
    """Create new object store container"""
    try:
        conn.object_store.create_container(name=container_name)
        print(f"Openstack_Swift:  Container {container_name} has been created"
              " in the object store")
        conn.set_container_access(name=container_name, access="public")
    except Exception as e:
        print("Openstack_Swift ERROR:  Cannot create container"
              f" {container_name} it already exists")
        print(f"Openstack_Swift ERROR:  {e}")


def delete_container(container_name):
    """Delete container from object store"""
    if search_containers(container_name):
        conn.delete_container(container_name)
        print(f"Openstack_Swift:  {container_name} container has been deleted"
              " from the object store")
    else:
        print("Openstack_Swift ERROR:  Cannot delete container"
              f" {container_name} it doesn't exist")


def upload_objs(container_name, dir):
    """Create directory markers and upload objects"""
    # Collect all the files and folders in the given directory
    objs = []
    dir_markers = []
    for (_dir, _ds, _fs) in walk(dir):
        if not (_ds + _fs):
            dir_markers.append(_dir)
        else:
            objs.extend([join(_dir, _f) for _f in _fs])

    # Create directory markers for folder structure
    dir_markers = [
        conn.create_directory_marker_object(
            container_name,
            d,
            ) for d in dir_markers
    ]

    # Create objects
    objs = [
        conn.create_object(
            container_name,
            o,
            data=o
            ) for o in objs
    ]

    objects = conn.list_objects(container_name)

    print("Openstack_Swift:  The following objects have been uploaded to the"
          f" container {container_name}:")
    for obj in objects:
        print(f"  - {obj.name}")


def delete_objs(container_name):
    """Delete container objects"""
    try:
        objects = conn.list_objects(container_name)
        print("Openstack_Swift:  The following objects were deleted from the"
              f" {container_name} container:")
        for obj in objects:
            conn.delete_object(container_name, str(obj.name))
            print(f"  - {obj.name}")
    except Exception as e:
        print(f"Openstack_Swift ERROR:  Cannot delete container objects"
              f" in {container_name} the container doesn't exist")
        print(f"Openstack_Swift ERROR:  {e}")


def search_containers(container_name):
    """Search if container exists"""
    print(f"Openstack_Swift:  Searching for {container_name} container...")
    container_exists = conn.search_containers(name=container_name)
    return(container_exists)


def main():
    # Create main dictionary and load templates
    swift_dict = {}
    heat_params = load_template(main_template)
    global_params = load_template(globals_template)

    # Update main dictionary and update keys and values loaded from templates
    swift_dict.update({'swift_action':
                      global_params['swift']['action']})
    swift_dict.update({'container_name':
                      heat_params['parameters']['container_name']['default']})
    swift_dict.update({'assets_dir': assets_dir})

    # Swift actions based on globals template data
    if swift_dict['swift_action'] == "create":
        create_container(swift_dict['container_name'])
        upload_objs(swift_dict['container_name'], swift_dict['assets_dir'])
    if swift_dict['swift_action'] == "delete":
        delete_objs(swift_dict['container_name'])
        delete_container(swift_dict['container_name'])
    if swift_dict['swift_action'] == "update":
        upload_objs(swift_dict['container_name'], swift_dict['assets_dir'])
        print("Openstack_Swift:  Updated"
              f" {swift_dict['container_name']} container objects")


if __name__ == '__main__':
    print("***  Begin Swift object storage script  ***\n")
    globals_template = 'globals.yaml'
    template_dir = load_template('globals.yaml')['openstack']['template_dir']
    main_template = f'{template_dir}/main.yaml'
    assets_dir = load_template('globals.yaml')['swift']['asset_dir']
    config = loader.OpenStackConfig()
    conn = openstack.connect(cloud=load_template
                             (globals_template)['global']['cloud'])
    openstack.enable_logging(debug=load_template
                             (globals_template)['global']['debug'])
    main()
    print("\n*** End Swift object storage script  ***")
