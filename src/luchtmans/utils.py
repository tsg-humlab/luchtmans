import re
import datetime

from django.db.models import Subquery, FloatField, Q


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


def and_or_to_q(search_string: str, field_name:str, AND: str= 'AND', OR: str= 'OR') -> Q:
    """Convert a search string to an AND and OR queryset"""
    AND_esc = re.escape(AND)
    OR_esc = re.escape(OR)
    search_string = search_string.strip()
    search_string = re.sub(rf'^(({AND_esc}|{OR_esc})\s+)*', '', search_string)
    search_string = re.sub(rf'(\s+({AND_esc}|{OR_esc}))*$', '', search_string)
    search_list = re.split(rf'\s+({AND_esc}|{OR_esc})(?=\s)', search_string)
    search_list = list(map(str.strip, search_list))
    print(search_list)

    def make_q(term):
        return ~Q(**{f'{field_name}__icontains': term[1:]}) if term.startswith('-') \
            else Q(**{f'{field_name}__icontains': term})

    q = make_q(search_list.pop(0))
    while search_list:
        operator = search_list.pop(0)
        new_q = make_q(search_list.pop(0))
        if operator == AND:
            q &= new_q
        elif operator == OR:
            q |= new_q
    return q