import re
import datetime


def get_nested_object(data, path, *args):
    """Give a path, return the value"""
    try:
        for key in path:
            data = data[key]
        return data
    except (KeyError, IndexError) as error:
        if args:
            return args[0]
        raise error


def str_to_date(value):
    """Convert a string to a datetime object if possible. Otherwise return the original value."""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    return value