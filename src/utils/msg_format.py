"""
Contains all the main functions for message formatting and event dispatching.
"""

from colorama import Fore
try:
    from src.utils.events import dispatcher
except ImportError:
    from utils.events import dispatcher


def error_msg(text: str | list | dict,
              endpoint='') -> None:
    """
    Prints an error message based on the input error and dispatches event.
    """
    endpoint_name = endpoint
    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.RED + endpoint + "[ERROR]".ljust(12) + Fore.RESET, end='')
    print(text)
    dispatcher.dispatch("ERROR", str(text), endpoint=endpoint_name)


def info_msg(text: str | list | dict,
             endpoint='',
             debug=False):
    """
    Prints informational messages based on the type of input provided.
    """
    if not debug:
        return

    endpoint_name = endpoint
    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.BLUE + endpoint + "[INFO]".ljust(12) + Fore.RESET, end='')
    print(text)
    dispatcher.dispatch("DEBUG", str(text), endpoint=endpoint_name)


def success_msg(text: str | list | dict,
                endpoint='') -> None:
    """
    Prints a success message to the console with an optional endpoint prefix.
    """
    endpoint_name = endpoint
    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.GREEN + endpoint + "[SUCCESS]".ljust(12) + Fore.RESET, end='')
    print(text)
    dispatcher.dispatch("SUCCESS", str(text), endpoint=endpoint_name)


def general_msg(text: str | list | dict,
                endpoint='') -> None:
    """
    Prints the given text or list or dictionary to the console with an optional endpoint prefix.
    """
    endpoint_name = endpoint
    if endpoint:
        endpoint = endpoint.ljust(12)

    print(Fore.YELLOW + endpoint + "[INFO]".ljust(12) + Fore.RESET, end='')
    print(text)
    dispatcher.dispatch("INFO", str(text), endpoint=endpoint_name)
