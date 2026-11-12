"""
Loads a template file and returns a dictionary
"""
import os
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from yaml import safe_load
from utils import msg_format


def load_template(template_name: str,
                  template_dir: str = '.') -> dict:
    """Render a Jinja template, parse its YAML, and return a mapping.

    Args:
        template_name (str): The template filename.
        template_dir (str, optional): The directory containing the template files. Defaults to '.'.

    Returns:
        dict: The rendered YAML mapping.

    Raises:
        ValueError: If the template has Jinja syntax errors or does not render
            to a YAML mapping.
    """

    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        rendered = template.render()
    except TemplateSyntaxError as error:
        raise ValueError(
            f"Template '{template_name}' has a syntax error: {error.message}"
        ) from error

    parameters = safe_load(rendered)
    if not isinstance(parameters, dict):
        raise ValueError(
            f"Template '{template_name}' must render to a YAML mapping."
        )

    return parameters


def load_yaml_file(file_name: str,
                   template_dir: str | None = None,
                   debug: bool = False) -> dict:
    """Load a Jinja-rendered YAML mapping from the specified directory.

    Parameters:
        file_name (str): The name of the YAML file to load.
        template_dir (str, optional): Directory containing the file.
        debug (bool): Flag to indicate whether debug messages should be displayed.

    Returns:
        dict: The loaded YAML mapping.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension or contents are invalid.
    """

    endpoint = 'Templates'

    if os.path.splitext(file_name)[1].lower() not in {'.yaml', '.yml'}:
        raise ValueError(f"'{file_name}' is not a YAML file.")

    if template_dir:
        yaml_file_path = f"{template_dir}/{file_name}"
    else:
        template_dir = '.'
        yaml_file_path = file_name

    if not os.path.exists(yaml_file_path):
        raise FileNotFoundError(f"Cannot find file '{yaml_file_path}'.")

    if os.path.getsize(yaml_file_path) == 0:
        raise ValueError(f"The file '{yaml_file_path}' is empty.")

    msg_format.general_msg(f"Loading file '{yaml_file_path}'...",
                           endpoint)
    yaml_dict = load_template(file_name,
                              template_dir)

    msg_format.success_msg(f"'{yaml_file_path}' loaded.",
                           endpoint)
    msg_format.info_msg(yaml_dict,
                        endpoint,
                        debug)

    return yaml_dict
