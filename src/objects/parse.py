"""
Helper functions for parsing templates
"""


def expand_instances(data: dict,
                     default: dict) -> list | dict:
    """
    Recursively expands instances in dictionaries and lists

    Args:
        data (dict or list): The dictionary or list to expand instances in
        default (dict or list): The default value to use if the instance is not found

    Returns:
        dict or list: The expanded dictionary or list
    """
    data = recursive_update(data, default)
    count = data.get('count')

    if not count:
        return data

    return_data = []
    for index in range(1, count + 1):
        copy = replace_recursively(data, str(index))
        return_data.append(copy)

    return return_data


def recursive_update(d: dict,
                     u: dict) -> dict:
    """
    Recursively updates a dictionary with the key-value pairs from another dictionary.

    Parameters:
    - d (dict): The dictionary to be updated.
    - u (dict): The dictionary containing the updates.

    Returns:
    - dict: The updated dictionary after applying the recursive updates.
    """
    copy = d.copy()
    for k, v in u.items():
        if isinstance(v, dict):
            copy[k] = recursive_update(copy.get(k, {}), v)
        elif isinstance(v, list):
            if k in copy and isinstance(copy[k], list):
                copy[k].extend(v)
            else:
                copy[k] = v
        else:
            copy[k] = v
    return copy


def replace_recursively(data: dict,
                        repl: str,
                        match: str = '%index%') -> dict:
    """
    Recursively replaces occurrences of a match string in strings within the input data with the specified replacement string.
    This function ensures that the match string is replaced only in strings and retains the original structure of dictionaries
    and lists, handling nested structures as well. The original input data is not modified.

    Args:
        data: The input data, which could be a dictionary, list, string, or any other type.
        repl: The replacement value to use in place of the match string.
        match: The string to match for replacement (default is '%index%').

    Returns:
        A new data structure with the match string replaced by the actual replacement value within strings.
    """
    if isinstance(data, dict):
        return {k: replace_recursively(v, repl, match) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_recursively(item, repl, match) for item in data]
    elif isinstance(data, str):
        return data.replace(match, repl)
    else:
        return data


def clean_dict(data: dict | list) -> dict | list:
    """
    A recursive function that cleans a nested dictionary or list
    by removing any empty values (None, "", [], {}). 

    Args:
        data (dict or list): The dictionary or list to clean.

    Returns:
        dict or list: The cleaned dictionary or list.
    """

    if isinstance(data, dict):
        return {
            str(key): clean_dict(value)
            for key, value in sorted(data.items())
            if value
        }
    elif isinstance(data, list):
        return sorted([
            clean_dict(item)
            for item in data
            if item
        ])
    else:
        return str(data)
