import argparse


def parser():
    provision_args = argparse.ArgumentParser(
                        prog = "Range Provisioner",
                        description = "Povision Openstack resources.")
    
    provision_args.add_argument("-p", "--pipeline", action="store_true", help="Use ONLY if using Pipeline vars defined in globals.yaml")
    provision_args.add_argument("-a", "--action", action="store", help="Action to take (Create/Delete)")
    provision_args.add_argument("-t", "--type", action="store", help="Provision Type (object, heat, guac)")
    provision_args.add_argument("-cn", "--container_name", action="store", help="Object Container Name)")
    provision_args.add_argument("-td", "--template_dir", action="store", help="Main Heat Template Directory")
    provision_args.add_argument("-sd", "--secgroup_dir", action="store", help="Secgroup Heat Template Directory")
    provision_args.add_argument("-as", "--assets_dir", action="store", help="Assets Dir for Object Store Upload" )
    args = provision_args.parse_args()

    return args

