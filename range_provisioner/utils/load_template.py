from munch import Munch
from yaml import safe_load
from utils.msg_format import error_msg, info_msg, success_msg

def load_template(template):
    """Load Template"""
    with open(template, 'r') as file:
        params_template = Munch(safe_load(file))    
    return params_template

def load_global():
    try:
        global_dict = load_template("globals.yaml")
    except Exception as e:
        error_msg(f"Cannot load global template \n  ({e})")
        global_dict = None        
    return global_dict

def load_heat(global_dict=load_global()):
    try:
        heat_dict = load_template(f"{global_dict.heat['template_dir']}/main.yaml")
    except Exception as e:
        error_msg(f"Cannot load main template \n  ({e})")
        heat_dict = None
    return heat_dict

def load_sec(global_dict=load_global()):
    try:
        secgroup_dict = load_template(f"{global_dict.heat['template_dir']}/sec.yaml")
    except Exception as e:
        error_msg(f"Cannot load secgroup template \n  ({e})")
        secgroup_dict = None
    return secgroup_dict



