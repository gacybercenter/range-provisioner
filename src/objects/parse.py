"""
Helper functions for parsing templates
"""

import re


def expand_instances(data: dict,
                     default: dict) -> list:
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
        return [data]

    return_data = []
    for index in range(1, count + 1):
        copy = replace_recursively(data, index)
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


def replace_recursively(data: dict, index: int, match: str = '%index%') -> dict:
    """
    Recursively replaces occurrences of a match string followed by an optional
    + or - and a number in strings within the input data with the index adjusted by the specified number.
    This function ensures that matching expressions are replaced only in strings and retains the original
    structure of dictionaries and lists, handling nested structures as well. The original input data is not modified.

    Args:
        data: The input data, which could be a dictionary, list, string, or any other type.
        index: The index value to use for replacement.
        match: The string to match for replacement (default is '%index%').

    Returns:
        A new data structure with matching expressions replaced by the actual index value adjusted within strings.
    """
    if isinstance(data, dict):
        return {k: replace_recursively(v, index, match) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_recursively(item, index, match) for item in data]
    elif isinstance(data, str):
        def replace_match(match_obj):
            operator = match_obj.group(2)
            number = int(match_obj.group(3)) if match_obj.group(3) else 0
            new_index = index + number if operator == '+' else index - number if operator == '-' else index
            return str(new_index)

        pattern = re.compile(fr"({re.escape(match)})([+-])?(\d+)?")
        return pattern.sub(replace_match, data)
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
