import re
import datetime

from django.db.models import Subquery, FloatField


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


class SubqueryMedian(Subquery):
    template = '(SELECT PERCENTILE_CONT(.50) WITHIN GROUP (ORDER BY %(field_name)s) FROM (%(subquery)s) _median)'
    output_field = FloatField()

    def __init__(self, queryset, output_field=None, **extra):
        extra['field_name'] = queryset._fields[0]
        super().__init__(queryset, output_field, **extra)
