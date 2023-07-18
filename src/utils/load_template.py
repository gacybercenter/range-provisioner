from munch import Munch
from yaml import safe_load
from utils.msg_format import error_msg, info_msg, success_msg



def load_template(template):
    """ 
    Load a template file and return a dictionary
    
    Args:
        template (str): The path to the template file.
    Returns:
        dict: A dictionary containing the template parameters.
    """
    try:
        info_msg(f"Loading {template}")
        with open(template, 'r') as file:
            parameters = Munch(safe_load(file))  
    except Exception as e:
        error_msg(f"Cannot load template \n  ({e})")
        return None
    return parameters

def load_global():
    try:
        globals_dict = load_template("globals.yaml")
        success_msg("Globals loaded")
    except Exception as e:
        error_msg(e)
        return None        
    return globals_dict

def load_heat(heat_template_dir):
    try:
        heat_dict = load_template(f"{heat_template_dir}/main.yaml")
        success_msg(f"{heat_template_dir}/main.yaml loaded")
    except Exception as e:
        error_msg(e)
        return None 
    return heat_dict


def load_sec(heat_template_dir):
    try:
        security_dict = load_template(f"{heat_template_dir}/sec.yaml")
        success_msg(f"{heat_template_dir}/sec.yaml loaded")
    except Exception as e:
        error_msg(e)
        return None 
    return security_dict

def load_env(heat_template_dir):
    try:
        environment_dict = load_template(f"{heat_template_dir}/env.yaml")
        success_msg(f"{heat_template_dir}/env.yaml loaded")
    except Exception as e:
        error_msg(e)
        return None 
    return environment_dict
