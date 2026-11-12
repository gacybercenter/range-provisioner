"""
Helper functions for parsing templates
"""

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
    if not isinstance(u, dict):
        return copy
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
