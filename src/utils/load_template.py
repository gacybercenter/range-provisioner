from munch import Munch
from yaml import safe_load
from utils.msg_format import error_msg, info_msg, general_msg, success_msg


def load_template(template,
                  debug=False):
    """ 
    Load a template file and return a dictionary
    
    Args:
        template (str): The path to the template file.
    Returns:
        dict: A dictionary containing the template parameters.
    """
    try:
        info_msg(f"Loading {template}", debug)
        with open(template, 'r', encoding='utf-8') as file:
            parameters = Munch(safe_load(file))
    except FileNotFoundError:
        info_msg(f"Cannot find {template}")
        return {}
    except Exception as error:
        error_msg(f"Cannot load template \n  ({error})")
        return {}
    return parameters

def load_global(debug=False):
    """
    Load the global variables from the "globals.yaml" template file.

    Returns:
        dict: A dictionary containing the global variables loaded from the template file.

    Raises:
        Exception: If there is an error while loading the template file.
    """
    globals_dict = load_template("globals.yaml",
                                 debug)
    if globals_dict:
        success_msg("Globals loaded")
    else:
        general_msg("No globals found")
    return globals_dict

def load_heat(heat_template_dir,
              debug=False):
    """
    Load heat template from the specified directory.

    Parameters:
    - heat_template_dir (str): The directory path where the heat template is located.

    Returns:
    - heat_dict (dict): The loaded heat template as a dictionary.

    This function loads the heat template from the specified directory by calling the
    `load_template`function with the path to the `main.yaml` file. If the loading is
    successful, a success message is printed. If an exception occurs during the loading
    process, an error message is printed and {} is returned. The loaded heat template
    is returned as a dictionary.

    Note: The `load_template` and `general_msg` functions are assumed to be defined elsewhere.
    """
    heat_dict = load_template(f"{heat_template_dir}/main.yaml",
                              debug)
    if heat_dict:
        success_msg(f"{heat_template_dir}/main.yaml loaded")
    else:
        general_msg(f"{heat_template_dir}/main.yaml not found")
    return heat_dict


def load_sec(heat_template_dir,
             debug=False):
    """
    Load the security template file from the specified heat template directory.

    Parameters:
        heat_template_dir (str): The directory path where the heat template files are located.

    Returns:
        dict: A dictionary containing the loaded security template, or {} if an error occurred.
    """
    security_dict = load_template(f"{heat_template_dir}/sec.yaml",
                                  debug)
    if security_dict:
        success_msg(f"{heat_template_dir}/sec.yaml loaded")
    else:
        general_msg(f"{heat_template_dir}/sec.yaml not found")
    return security_dict


def load_env(heat_template_dir,
             debug=False):
    """
    Load the environment dictionary from the specified heat template directory.

    Parameters:
        heat_template_dir (str): The directory containing the heat template.

    Returns:
        environment_dict (dict): The environment dictionary loaded from the heat template.
        {}: If there was an error loading the template or any exception occurred.
    """
    environment_dict = load_template(f"{heat_template_dir}/env.yaml",
                                    debug)
    if environment_dict:
        success_msg(f"{heat_template_dir}/env.yaml loaded")
    else:
        general_msg(f"{heat_template_dir}/env.yaml not found")
    return environment_dict


def load_users(heat_template_dir,
               debug=False):
    """
    Load users from a Heat template directory.

    Args:
        heat_template_dir (str): The directory path where the Heat template is located.

    Returns:
        dict: A dictionary containing the loaded environment configuration from the Heat template.
            If an error occurs during the loading process, {} is returned.
    """
    environment_dict = load_template(f"{heat_template_dir}/users.yaml",
                                    debug)
    if environment_dict:
        success_msg(f"{heat_template_dir}/users.yaml loaded")
    else:
        general_msg(f"{heat_template_dir}/users.yaml not found")
    return environment_dict
