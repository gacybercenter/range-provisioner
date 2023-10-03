"""
Contains all the main functions for message formatting
"""

from colorama import Fore
from pprint import pprint


def error_msg(text: str | list | dict,
              endpoint='') -> None:
    """
    Prints an error message based on the input error.

    Parameters:
     - text (str | list | dict): The error message to be printed.
     - endpoint (str): The endpoint where the error occurred

    Returns:
        None
    """

    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.RED + endpoint + "[ERROR]".ljust(12) + Fore.RESET, end='')

    if isinstance(text, str):
        print(text)
    else:
        print()
        pprint(text, indent=4)


def info_msg(text: str | list | dict,
             endpoint='',
             debug=False):
    """
    Prints informational messages based on the type of input provided.

    Parameters:
    - text (str | list | dict): The info message(s) to be printed.
    - endpoint (str): The endpoint where the message originated.
    - debug (bool): A boolean indicating whether to print the message(s) or not.

    Returns:
        None
    """

    if not debug:
        return

    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.BLUE + endpoint + "[INFO]".ljust(12) + Fore.RESET, end='')

    if isinstance(text, str):
        print(text)
    else:
        print()
        pprint(text, indent=4)


def success_msg(text: str | list | dict,
                endpoint='') -> None:
    """
    Prints a success message to the console with an optional endpoint prefix.

    Parameters:
    - text: A string, list, or dictionary containing the message(s) to be printed.
    - endpoint: An optional string representing the endpoint prefix.

    Returns:
    None
    """

    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.GREEN + endpoint + "[SUCCESS]".ljust(12) + Fore.RESET, end='')

    if isinstance(text, str):
        print(text)
    else:
        print()
        pprint(text, indent=4)


def general_msg(text: str | list | dict,
                endpoint='') -> None:
    """
    Prints the given text or list or dictionary to the console with an optional endpoint prefix.

    Parameters:
        - text (str | list | dict): The text or list or dictionary to be printed.
        - endpoint (str): The optional endpoint prefix to be added to the printed text.

    Returns:
        None
    """

    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.YELLOW + endpoint + "[INFO]".ljust(12) + Fore.RESET, end='')

    if isinstance(text, str):
        print(text)
    else:
        print()
        pprint(text, indent=4)
