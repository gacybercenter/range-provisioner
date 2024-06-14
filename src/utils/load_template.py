"""
Loads a template file and returns a dictionary
"""
import os
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from yaml import safe_load
from utils import msg_format

def load_template(template_name: str,    
                  template_dir: str = '.') -> dict | None:
    """
    Load a template file and return a dictionary

    Args:
        template (str): The path to the template file.
        template_dir (str, optional): The directory containing the template files. Defaults to '.'.
        debug (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        dict: A dictionary containing the template parameters.
    """

    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        parameters = safe_load(template.render())

    except TemplateSyntaxError as error:
        error_message = error.message
        raise ValueError(f"Template {template} has a syntax error: {error_message}")

    except Exception as error:
        raise error

    return parameters

def load_yaml_file(file_name: str,
                   heat_template_dir: str = '.',
                   debug: bool = False) -> dict | None:
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

    if not file_name.split('.')[-1] in ['yaml', 'yml']:
        msg_format.general_msg(f"'{file_name}' is not a YAML file", endpoint)
        return {}

    yaml_file_path = f"{heat_template_dir}/{file_name}"

    if not os.path.exists(yaml_file_path):
        msg_format.general_msg(f"Cannot find '{yaml_file_path}'", endpoint)
        return {}

    if os.path.getsize(yaml_file_path) == 0:
        msg_format.general_msg(f"The file '{yaml_file_path}' is empty", endpoint)
        return {}

    msg_format.general_msg(f"Loading '{yaml_file_path}'", endpoint)
    yaml_dict = load_template(file_name, heat_template_dir)

    if yaml_dict:
        msg_format.success_msg(f"'{yaml_file_path}' loaded", endpoint)
        msg_format.info_msg(yaml_dict, endpoint, debug)
    else:
        msg_format.error_msg(f"'{yaml_file_path}' not found", endpoint)

    return yaml_dict
