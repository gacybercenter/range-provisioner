"""
Loads a template file and returns a dictionary
"""
from jinja2 import Template
from yaml import safe_load
from utils.msg_format import info_msg, general_msg, success_msg


def load_template(template,
                  debug=False):
    """ 
    Load a template file and return a dictionary

    Args:
        template (str): The path to the template file.
    Returns:
        dict: A dictionary containing the template parameters.
    """

    endpoint = 'Templates'

    info_msg(f"Loading {template}",
                endpoint,
                debug)

    try:
        with open(template, 'r', encoding='utf-8') as file:
            file_content = file.read()
        
        if not file_content:
            general_msg(f"Template {template} is empty",
                        endpoint)
            return {}

        parameters = safe_load(Template(file_content).render())

    except FileNotFoundError:
        info_msg(f"Cannot find {template}",
                 endpoint,
                 debug)
        return {}

    except Exception as error:
        raise error

    return parameters


def load_yaml_file(file_name,
                   heat_template_dir='.',
                   debug=False):
    """
    Load a YAML file from the specified directory.

    Parameters:
        heat_template_dir (str): The directory path where the heat template files are located.
        file_name (str): The name of the YAML file to load.
        debug (bool): Flag to indicate whether debug messages should be displayed.

    Returns:
        dict: A dictionary containing the loaded YAML file, or {} if an error occurred.
    """

    endpoint = 'Templates'
    yaml_file_path = f"{heat_template_dir}/{file_name}"
    yaml_dict = load_template(yaml_file_path, debug)

    if yaml_dict:
        success_msg(f"'{yaml_file_path}' loaded", endpoint)
    else:
        general_msg(f"'{yaml_file_path}' not found", endpoint)

    return yaml_dict
